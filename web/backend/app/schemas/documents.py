import re


def validate_document(value: str, *, cnpj: bool = False) -> str:
    size = 14 if cnpj else 11
    mask = r'[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}' if cnpj else r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}'
    if not (re.fullmatch(rf'[0-9]{{{size}}}', value) or re.fullmatch(mask, value)):
        raise ValueError('Documento inválido')
    digits = re.sub(r'[^0-9]', '', value)
    if len(set(digits)) == 1:
        raise ValueError('Documento inválido')
    base = [int(digit) for digit in digits[:-2]]
    for _ in range(2):
        weights = ([6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][-len(base):]
                   if cnpj else list(range(len(base) + 1, 1, -1)))
        remainder = sum(digit * weight for digit, weight in zip(base, weights)) % 11
        base.append(0 if remainder < 2 else 11 - remainder)
    if ''.join(map(str, base)) != digits:
        raise ValueError('Documento inválido')
    return digits
