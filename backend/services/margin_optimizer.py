import pandas as pd

CLASSES = ["A+", "A", "B", "C"]
MAX_ITERATIONS = 10


def optimize_margins(
    df: pd.DataFrame,
    desired_increase: float,
    max_increases: dict[str, float],
) -> tuple[pd.DataFrame, float, str | None]:
    """
    Calculate suggested margins per product.

    Args:
        df: DataFrame with columns Venda (R$), Margem Atual, ABC
        desired_increase: target overall weighted margin increase in pp
        max_increases: {"A+": float, "A": float, "B": float, "C": float}

    Returns:
        (df_with_suggestions, achieved_wam, warning_or_None)
    """
    df = df.copy()

    df_classified = df[df["ABC"].isin(CLASSES)].copy()

    if df_classified.empty:
        df["Margem Sugerida"] = df["Margem Atual"]
        current_wam = _weighted_avg_margin(df)
        return df, current_wam, "Nenhum produto classificado na Curva ABC."

    total_sales = df_classified["Venda (R$)"].sum()
    current_wam = (df_classified["Venda (R$)"] * df_classified["Margem Atual"]).sum() / total_sales

    class_sales = {c: df_classified.loc[df_classified["ABC"] == c, "Venda (R$)"].sum() for c in CLASSES}
    class_weight = {c: class_sales[c] / total_sales for c in CLASSES}

    max_achievable = sum(class_weight[c] * max_increases.get(c, 0.0) for c in CLASSES)

    warning = None
    if desired_increase > max_achievable + 1e-9:
        warning = (
            f"Aumento desejado de {desired_increase:.2f}pp não é atingível com as restrições configuradas. "
            f"Melhor resultado possível: +{max_achievable:.2f}pp. Aplicando o máximo permitido."
        )
        effective_increase = max_achievable
    else:
        effective_increase = desired_increase

    deltas = _allocate_deltas(class_weight, max_increases, effective_increase)

    df["Margem Sugerida"] = df.apply(
        lambda row: row["Margem Atual"] + deltas.get(row["ABC"], 0.0)
        if row["ABC"] in CLASSES
        else row["Margem Atual"],
        axis=1,
    )
    # Never suggest below current
    df["Margem Sugerida"] = df[["Margem Atual", "Margem Sugerida"]].max(axis=1)

    achieved_wam = _weighted_avg_margin(df[df["ABC"].isin(CLASSES)])

    return df, achieved_wam, warning


def _allocate_deltas(
    class_weight: dict[str, float],
    max_increases: dict[str, float],
    target_increase: float,
) -> dict[str, float]:
    """Iterative proportional allocation with per-class caps."""
    deltas = {c: 0.0 for c in CLASSES}
    remaining = target_increase
    uncapped = set(CLASSES)

    for _ in range(MAX_ITERATIONS):
        if not uncapped or remaining <= 1e-9:
            break

        uncapped_weight = sum(class_weight[c] for c in uncapped)
        if uncapped_weight <= 1e-9:
            break

        newly_capped = set()
        proposed = {}
        for c in uncapped:
            proportion = class_weight[c] / uncapped_weight
            proposed[c] = remaining * proportion / class_weight[c] if class_weight[c] > 1e-9 else 0.0
            if proposed[c] >= max_increases.get(c, 0.0):
                proposed[c] = max_increases.get(c, 0.0)
                newly_capped.add(c)

        for c in uncapped:
            deltas[c] = proposed[c]

        if not newly_capped:
            break

        capped_contribution = sum(class_weight[c] * deltas[c] for c in newly_capped)
        remaining -= capped_contribution
        uncapped -= newly_capped

    return deltas


def _weighted_avg_margin(df: pd.DataFrame) -> float:
    total_sales = df["Venda (R$)"].sum()
    if total_sales == 0:
        return 0.0
    col = "Margem Sugerida" if "Margem Sugerida" in df.columns else "Margem Atual"
    return (df["Venda (R$)"] * df[col]).sum() / total_sales


def compute_summary(df: pd.DataFrame, current_wam: float, target_wam: float, achieved_wam: float) -> dict:
    breakdown = {}
    for cls in CLASSES:
        mask = df["ABC"] == cls
        if mask.any():
            cls_df = df[mask]
            avg_increase = (cls_df["Margem Sugerida"] - cls_df["Margem Atual"]).mean()
            breakdown[cls] = {"count": int(mask.sum()), "avg_increase": round(avg_increase, 4)}

    return {
        "total_products": len(df),
        "current_weighted_margin": round(current_wam, 4),
        "target_weighted_margin": round(target_wam, 4),
        "achieved_weighted_margin": round(achieved_wam, 4),
        "abc_breakdown": breakdown,
    }
