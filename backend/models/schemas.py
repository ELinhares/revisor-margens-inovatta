from pydantic import BaseModel
from typing import Optional


class ABCBreakdownItem(BaseModel):
    count: int
    avg_increase: float


class ProcessingSummary(BaseModel):
    total_products: int
    current_weighted_margin: float
    target_weighted_margin: float
    achieved_weighted_margin: float
    abc_breakdown: dict[str, ABCBreakdownItem]


class ValidateResponse(BaseModel):
    status: str
    all_columns: list[str]
    inferred_mapping: dict[str, Optional[str]]
    columns_found: list[str]
    missing_columns: list[str]
    total_rows: int
    preview: list[dict]


class ProcessResponse(BaseModel):
    status: str
    download_signed_url: Optional[str] = None
    original_gcs_uri: Optional[str] = None
    processed_gcs_uri: Optional[str] = None
    summary: Optional[ProcessingSummary] = None
    warning: Optional[str] = None
    detail: Optional[str] = None
