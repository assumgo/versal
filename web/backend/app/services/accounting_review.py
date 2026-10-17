"""Pure read-time rules from desktop refresh_param_contabil, not rubric saves."""
import re

COR_REQUIRED_ACCOUNTS = {'4211020001', '4211010001'}


def flag_enabled(value: int | None) -> bool:
    # Legacy SQLite flags are integer columns; nonzero integers are true.
    return bool(value)


def effective_cc(plan_flag: int | None, rubric_flag: int | None) -> bool:
    return bool(plan_flag) or flag_enabled(rubric_flag)


def effective_cor(account: str | None, plan_flag: int | None, rubric_flag: int | None, employee_linked: bool) -> bool:
    compat = employee_linked and digits(account) in COR_REQUIRED_ACCOUNTS
    return bool(max(plan_flag or 0, int(flag_enabled(rubric_flag)), int(compat)))


def digits(value: str | None) -> str:
    return re.sub(r'\D', '', value or '')


def review_history(value: str | None) -> str:
    value = digits(value)
    return value[-9:].zfill(9) if value else ''
