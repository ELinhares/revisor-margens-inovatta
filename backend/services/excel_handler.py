import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

REQUIRED_COLUMNS = ["Código do Produto", "Venda (R$)", "Margem Atual"]

COLUMN_ALIASES = {
    "Produto (descrição)": "Produto",
    "Produto (Descrição)": "Produto",
    "produto": "Produto",
    "Descrição": "Produto",
    "descricao": "Produto",
    "codigo": "Código do Produto",
    "Codigo do Produto": "Código do Produto",
    "Código": "Código do Produto",
    "venda": "Venda (R$)",
    "Venda": "Venda (R$)",
    "Receita": "Venda (R$)",
    "margem": "Margem Atual",
    "Margem": "Margem Atual",
    "Margem (%)": "Margem Atual",
}

ALL_REQUIRED = REQUIRED_COLUMNS + ["Produto"]


def validate_and_read(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    # Apply aliases
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    missing = [c for c in ALL_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    df["Venda (R$)"] = pd.to_numeric(df["Venda (R$)"], errors="coerce").fillna(0.0)
    df["Margem Atual"] = pd.to_numeric(df["Margem Atual"], errors="coerce").fillna(0.0)

    return df.copy()


def check_columns(file_bytes: bytes) -> dict:
    """Return column validation info without raising."""
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    found = [c for c in ALL_REQUIRED if c in df.columns]
    missing = [c for c in ALL_REQUIRED if c not in df.columns]

    preview_cols = [c for c in ALL_REQUIRED if c in df.columns]
    preview = df[preview_cols].head(5).fillna("").to_dict(orient="records")

    return {
        "columns_found": found,
        "missing_columns": missing,
        "total_rows": len(df),
        "preview": preview,
    }


def write_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()

    col_order = ["Código do Produto", "Produto", "Venda (R$)", "Margem Atual", "ABC", "Margem Sugerida"]
    extra = [c for c in df.columns if c not in col_order]
    final_cols = [c for c in col_order if c in df.columns] + extra
    df = df[final_cols]

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Revisão de Margens")
        ws = writer.sheets["Revisão de Margens"]

        header_fill = PatternFill(start_color="0057B8", end_color="0057B8", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)

        for col_idx, col_name in enumerate(final_cols, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Format data rows
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                col_name = final_cols[cell.column - 1] if cell.column <= len(final_cols) else ""
                if col_name == "Venda (R$)":
                    cell.number_format = 'R$ #,##0.00'
                elif col_name in ("Margem Atual", "Margem Sugerida"):
                    cell.number_format = '0.00"%"'

        # Auto-fit column widths
        for col_idx, col_name in enumerate(final_cols, start=1):
            max_len = max(
                len(str(col_name)),
                *[len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(2, ws.max_row + 1)],
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 40)

        ws.freeze_panes = "A2"

    return output.getvalue()
