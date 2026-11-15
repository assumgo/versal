import re

NUMERIC_CODE = re.compile(r'^(\d+)$')


def next_numeric_codigo(existing: list[str | None], *, start: int, width: int = 6) -> str:
    """Próximo código numérico sequencial, com zero-padding."""
    max_n = start - 1
    for code in existing:
        match = NUMERIC_CODE.match((code or '').strip())
        if match:
            max_n = max(max_n, int(match.group(1)))
    next_n = max(max_n + 1, start)
    while True:
        candidate = f'{next_n:0{width}d}'
        if candidate not in {(c or '').strip() for c in existing}:
            return candidate
        next_n += 1
