from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('America/Sao_Paulo')


def today() -> date:
    return datetime.now(ZONE).date()


def now_utc() -> datetime:
    return datetime.now(ZoneInfo('UTC'))
