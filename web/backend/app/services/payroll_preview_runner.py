"""Bounded subprocess lifecycle for untrusted document parsing."""
import asyncio
from decimal import Decimal
import json
from pathlib import Path
import sys

from app.parsers.types import ParsedStatement
from app.services.payroll_preview_files import PreviewInputError, validate_result


class PreviewRunner:
    def __init__(self, timeout: float = 30):
        self.timeout = timeout
        self._slots = asyncio.Semaphore(2)

    async def run(self, path: Path, extension: str) -> ParsedStatement:
        if self._slots.locked():
            raise PreviewInputError(503, 'Duas leituras estão em andamento. Tente novamente em instantes.')
        await self._slots.acquire()
        process = None
        spawn = None
        try:
            async with asyncio.timeout(self.timeout):
                spawn = asyncio.create_task(asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'app.services.payroll_preview_worker', str(path.resolve()), extension,
                    cwd=str(Path(__file__).resolve().parents[2]),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                ))
                process = await asyncio.shield(spawn)
                stdout, _ = await process.communicate()
                if process.returncode:
                    raise ValueError('worker failed')
                envelope = json.loads(stdout)
                if 'error' in envelope:
                    error = envelope['error']
                    raise PreviewInputError(error['status'], error['message'])
                result = envelope['statement']
                validate_result(result)
                for person in result['colaboradores']:
                    person['liquido'] = Decimal(person['liquido'])
                    for rubric in person['rubricas']:
                        rubric['valor'] = Decimal(rubric['valor'])
                return result
        except TimeoutError:
            raise PreviewInputError(504, 'A leitura excedeu 30 segundos. Confira o documento ou tente um arquivo menor.') from None
        except PreviewInputError:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            raise PreviewInputError(400, 'Não foi possível concluir a leitura do documento.') from None
        finally:
            try:
                if process is None and spawn is not None:
                    try:
                        process = await asyncio.shield(spawn)
                    except OSError:
                        pass
                if process is not None:
                    if process.returncode is None:
                        try:
                            process.kill()
                        except ProcessLookupError:
                            pass
                    await asyncio.shield(process.wait())
            finally:
                self._slots.release()


preview_runner = PreviewRunner()
