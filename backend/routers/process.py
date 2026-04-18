from datetime import datetime
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.schemas import ProcessResponse, ValidateResponse
from services.abc_classifier import classify_abc
from services.excel_handler import check_columns, validate_and_read, write_excel
from services.gcs_service import upload_file
from services.margin_optimizer import compute_summary, optimize_margins

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_file(file: UploadFile = File(...)) -> ValidateResponse:
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=422, detail="O arquivo deve ser no formato Excel (.xlsx ou .xls).")

    file_bytes = await file.read()
    try:
        info = check_columns(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erro ao ler o arquivo: {exc}")

    status = "ok" if not info["missing_columns"] else "erro"
    return ValidateResponse(status=status, **info)


@router.post("/process", response_model=ProcessResponse)
async def process_file(
    cnpj: str = Form(...),
    razao_social: str = Form(...),
    desired_margin_increase: float = Form(...),
    max_increase_aplus: float = Form(...),
    max_increase_a: float = Form(...),
    max_increase_b: float = Form(...),
    max_increase_c: float = Form(...),
    file: UploadFile = File(...),
) -> ProcessResponse:
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=422, detail="O arquivo deve ser no formato Excel (.xlsx ou .xls).")

    file_bytes = await file.read()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    # 1. Read and validate
    try:
        df = validate_and_read(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 2. Classify ABC
    df = classify_abc(df)

    # 3. Optimize margins
    max_increases = {
        "A+": max_increase_aplus,
        "A": max_increase_a,
        "B": max_increase_b,
        "C": max_increase_c,
    }
    df_result, achieved_wam, warning = optimize_margins(df, desired_margin_increase, max_increases)

    total_sales = df_result[df_result["ABC"].isin(["A+", "A", "B", "C"])]["Venda (R$)"].sum()
    current_wam = (
        (df_result[df_result["ABC"].isin(["A+", "A", "B", "C"])]["Venda (R$)"]
         * df_result[df_result["ABC"].isin(["A+", "A", "B", "C"])]["Margem Atual"]).sum()
        / total_sales if total_sales > 0 else 0.0
    )
    target_wam = current_wam + desired_margin_increase

    summary_data = compute_summary(df_result, current_wam, target_wam, achieved_wam)

    # 4. Write Excel output
    processed_bytes = write_excel(df_result)

    # 5. Upload to GCS
    try:
        original_uri, _ = upload_file(file_bytes, cnpj, razao_social, "original.xlsx", timestamp)
        processed_uri, signed_url = upload_file(processed_bytes, cnpj, razao_social, "processed.xlsx", timestamp)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no Cloud Storage: {exc}")

    return ProcessResponse(
        status="success",
        download_signed_url=signed_url,
        original_gcs_uri=original_uri,
        processed_gcs_uri=processed_uri,
        summary=summary_data,
        warning=warning,
    )
