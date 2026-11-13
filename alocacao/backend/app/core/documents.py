import re

ONLY_DIGITS = re.compile(r'\D+')


def only_digits(value: str) -> str:
    return ONLY_DIGITS.sub('', value or '')


def normalize_cpf(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != 11:
        raise ValueError('CPF deve conter 11 dígitos')
    if digits == digits[0] * 11:
        raise ValueError('CPF inválido')
    return digits


def normalize_cpf_cnpj(value: str) -> str:
    digits = only_digits(value)
    if len(digits) not in (11, 14):
        raise ValueError('Informe CPF (11 dígitos) ou CNPJ (14 dígitos)')
    if digits == digits[0] * len(digits):
        raise ValueError('CNPJ/CPF inválido')
    return digits


def normalize_phone(value: str) -> str:
    digits = only_digits(value)
    if len(digits) < 10 or len(digits) > 13:
        raise ValueError('Celular deve ter entre 10 e 13 dígitos')
    return digits
