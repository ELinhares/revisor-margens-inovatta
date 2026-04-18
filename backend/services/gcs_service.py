import re
from datetime import datetime, timedelta
from google.auth.transport import requests as google_requests
from google.auth import compute_engine
from google.cloud import storage

BUCKET_NAME = "revisor-margens-inovatta"
CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SERVICE_ACCOUNT_EMAIL = "77708079939-compute@developer.gserviceaccount.com"


def _clean_cnpj(cnpj: str) -> str:
    return re.sub(r"[^\d]", "", cnpj)


def upload_file(
    file_bytes: bytes,
    cnpj: str,
    razao_social: str,
    filename: str,
    timestamp: str,
) -> tuple[str, str]:
    """Upload file to GCS and return (gs_uri, signed_url)."""
    # Use Compute Engine credentials with IAM signing (works on Cloud Run)
    auth_request = google_requests.Request()
    credentials = compute_engine.Credentials()
    credentials.refresh(auth_request)

    client = storage.Client(credentials=credentials)
    bucket = client.bucket(BUCKET_NAME)

    cnpj_clean = _clean_cnpj(cnpj)
    blob_path = f"{cnpj_clean}/{timestamp}/{filename}"
    blob = bucket.blob(blob_path)

    blob.metadata = {
        "cnpj": cnpj,
        "razao_social": razao_social,
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    blob.upload_from_string(file_bytes, content_type=CONTENT_TYPE)

    gs_uri = f"gs://{BUCKET_NAME}/{blob_path}"
    # Generate signed URL using IAM signing — required for Cloud Run (no private key)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
        service_account_email=SERVICE_ACCOUNT_EMAIL,
        access_token=credentials.token,
    )
    return gs_uri, signed_url
