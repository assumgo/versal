"""Metadata-only API contracts for persisted payroll imports."""
from pydantic import BaseModel


class PayrollImportCreated(BaseModel):
    import_id: int
    company_id: int
    competence: str
    filename: str
    size_bytes: int
    sha256: str
    imported_at: str
    employees: int
    rubrics: int
    totals_by_type: dict[str, str]
    net_total: str


class PayrollImportHistoryItem(BaseModel):
    import_id: int
    company_id: int
    competence: str | None
    filename: str | None
    status: str | None
    imported_at: str | None
    size_bytes: int | None
    sha256: str | None
    employees: int | None
    rubrics: int | None


class PayrollImportHistoryPage(BaseModel):
    items: list[PayrollImportHistoryItem]
    offset: int
    limit: int
    total: int
