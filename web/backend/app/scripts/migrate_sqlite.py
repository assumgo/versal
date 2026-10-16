"""One-time data migration. Dry-run by default; use --apply to commit."""
import argparse
import json
import os
from pathlib import Path
import sys
from typing import TextIO

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import get_engine
from app.migration.source import MigrationError
from app.migration.transfer import CommitUnknown, VERSION, migrate


def _reserve_report(path: Path, source: Path) -> TextIO:
    path = path.expanduser().resolve()
    origin = source.expanduser().resolve()
    protected = {Path(str(origin) + suffix) for suffix in ('', '-wal', '-shm', '-journal')}
    if path in protected:
        raise MigrationError('O relatório não pode substituir arquivos da origem')
    if any((parent / '.git').is_file() or (parent / '.git' / 'HEAD').is_file() for parent in path.parents):
        raise MigrationError('Salve o relatório fora do repositório')
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise MigrationError('Relatório deve ser novo e ter diretório existente com permissão de escrita') from None
    return os.fdopen(descriptor, 'w', encoding='utf-8')


def _write_report(stream: TextIO, report: dict) -> None:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
    stream.flush()
    os.fsync(stream.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Migração única SQLite → PostgreSQL; simula por padrão.')
    parser.add_argument('--source', required=True, type=Path, help='Arquivo SQLite do desktop fechado')
    parser.add_argument('--apply', action='store_true', help='Confirmar a carga após conferência integral')
    parser.add_argument('--report', type=Path, help='Relatório JSON novo, fora do repositório')
    args = parser.parse_args(argv)
    report = {'version': VERSION, 'mode': 'apply' if args.apply else 'simulate',
              'committed': False, 'status': 'failed'}
    stream = None
    code = 1
    try:
        if args.report is not None:
            stream = _reserve_report(args.report, args.source)
        settings = get_settings()
        if not settings.database_url:
            raise MigrationError('Configure DATABASE_URL para o PostgreSQL de destino')
        report = migrate(args.source, get_engine(), apply=args.apply)
        code = 0
        try:
            print('Carga confirmada e conferida' if report['committed'] else 'Simulação concluída; nenhum dado gravado')
            for table, count in report['counts'].items():
                print(f'{table}: {count}')
            if report['extra_tables']:
                print(f'Tabelas adicionais não migradas: {len(report["extra_tables"])}; consulte o relatório')
            print('Arquivos originais e vínculos de usuários não são migrados automaticamente')
        except OSError:
            code = 1
            report['status'] = 'output_failed'
            print('Carga confirmada; falha na saída do terminal. Não repita a carga.' if report['committed']
                  else 'Simulação concluída sem escrita; falha na saída do terminal', file=sys.stderr)
    except CommitUnknown:
        report.update(status='commit_unknown', committed=None)
        print('Resultado do commit indeterminado; confira o destino antes de repetir', file=sys.stderr)
    except MigrationError as exc:
        report['error'] = str(exc)
        print(str(exc), file=sys.stderr)
        print('Nenhuma carga confirmada nesta execução', file=sys.stderr)
    except ValidationError:
        code = 1
        report['error'] = 'Configuração inválida; verifique DATABASE_URL e JWT_SECRET_KEY'
        print(report['error'], file=sys.stderr)
    except (SQLAlchemyError, OSError, RuntimeError, ValueError):
        code = 1
        report['error'] = 'Falha na migração; confira conexão, permissões e esquema do destino'
        print(report['error'], file=sys.stderr)
        print('Nenhuma carga confirmada nesta execução', file=sys.stderr)
    finally:
        if stream is not None:
            try:
                _write_report(stream, report)
                stream.close()
            except OSError:
                if report['committed']:
                    print('Carga confirmada; falha ao salvar relatório. Não repita a carga.', file=sys.stderr)
                elif report['committed'] is None:
                    print('Commit indeterminado e falha ao salvar relatório; confira o destino', file=sys.stderr)
                else:
                    print('Falha ao salvar relatório; nenhuma carga confirmada', file=sys.stderr)
                code = 1
                try:
                    stream.close()
                except OSError:
                    pass
    return code


if __name__ == '__main__':
    raise SystemExit(main())
