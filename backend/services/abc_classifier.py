import pandas as pd

ABC_THRESHOLDS = {
    "A+": 40.0,
    "A": 80.0,
    "B": 95.0,
    "C": 100.0,
}


def classify_abc(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'ABC' column to df. Products with Venda=0 receive class 'N/A'."""
    df = df.copy()

    mask_valid = df["Venda (R$)"] > 0
    df_valid = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()

    if df_valid.empty:
        df["ABC"] = "N/A"
        return df

    df_valid = df_valid.sort_values("Venda (R$)", ascending=False)
    total_sales = df_valid["Venda (R$)"].sum()
    # Use cumulative % *before* including each product (starting position).
    # This ensures the most important product is always A+, even if it alone
    # accounts for >40% of total sales.
    df_valid["_cum_start"] = (df_valid["Venda (R$)"].cumsum() - df_valid["Venda (R$)"]) / total_sales * 100

    def _assign(cum_start: float) -> str:
        if cum_start < ABC_THRESHOLDS["A+"]:
            return "A+"
        if cum_start < ABC_THRESHOLDS["A"]:
            return "A"
        if cum_start < ABC_THRESHOLDS["B"]:
            return "B"
        return "C"

    df_valid["ABC"] = df_valid["_cum_start"].apply(_assign)
    df_valid.drop(columns=["_cum_start"], inplace=True)

    df_invalid["ABC"] = "N/A"

    result = pd.concat([df_valid, df_invalid]).reindex(df.index)
    return result
