import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pandas as pd
import pytest
from services.margin_optimizer import optimize_margins


def make_df_with_abc() -> pd.DataFrame:
    """
    4 products, one per ABC class, equal sales of 250 each (total 1000).
    Current WAM = (250*20 + 250*18 + 250*15 + 250*10) / 1000 = 15.75
    """
    return pd.DataFrame({
        "Código do Produto": ["P1", "P2", "P3", "P4"],
        "Produto": ["A", "B", "C", "D"],
        "Venda (R$)": [250.0, 250.0, 250.0, 250.0],
        "Margem Atual": [20.0, 18.0, 15.0, 10.0],
        "ABC": ["A+", "A", "B", "C"],
    })


MAX_INCREASES = {"A+": 5.0, "A": 4.0, "B": 3.0, "C": 2.0}


def test_margem_sugerida_column_created():
    df = make_df_with_abc()
    result, _, _ = optimize_margins(df, 2.0, MAX_INCREASES)
    assert "Margem Sugerida" in result.columns


def test_floor_never_below_current():
    df = make_df_with_abc()
    result, _, _ = optimize_margins(df, 0.0, MAX_INCREASES)
    assert (result["Margem Sugerida"] >= result["Margem Atual"]).all()


def test_achieved_wam_close_to_target():
    df = make_df_with_abc()
    desired = 2.0
    result, achieved_wam, warning = optimize_margins(df, desired, MAX_INCREASES)
    total_sales = result[result["ABC"].isin(["A+", "A", "B", "C"])]["Venda (R$)"].sum()
    current_wam = (df["Venda (R$)"] * df["Margem Atual"]).sum() / total_sales
    target = current_wam + desired
    assert abs(achieved_wam - target) < 0.05


def test_cap_respected_per_class():
    df = make_df_with_abc()
    max_inc = {"A+": 1.0, "A": 1.0, "B": 1.0, "C": 1.0}
    result, _, _ = optimize_margins(df, 1.0, max_inc)
    for cls, max_pp in max_inc.items():
        cls_mask = result["ABC"] == cls
        increases = result.loc[cls_mask, "Margem Sugerida"] - result.loc[cls_mask, "Margem Atual"]
        assert (increases <= max_pp + 1e-9).all(), f"Cap violated for class {cls}"


def test_warning_when_target_unreachable():
    df = make_df_with_abc()
    tiny_caps = {"A+": 0.1, "A": 0.1, "B": 0.1, "C": 0.1}
    _, _, warning = optimize_margins(df, 10.0, tiny_caps)
    assert warning is not None
    assert "não é atingível" in warning


def test_no_warning_when_reachable():
    df = make_df_with_abc()
    _, _, warning = optimize_margins(df, 1.0, MAX_INCREASES)
    assert warning is None


def test_zero_desired_increase_no_change():
    df = make_df_with_abc()
    result, _, _ = optimize_margins(df, 0.0, MAX_INCREASES)
    assert (result["Margem Sugerida"] == result["Margem Atual"]).all()


def test_na_class_products_unchanged():
    df = make_df_with_abc()
    df.loc[0, "ABC"] = "N/A"
    df.loc[0, "Margem Atual"] = 25.0
    result, _, _ = optimize_margins(df, 2.0, MAX_INCREASES)
    assert result.loc[0, "Margem Sugerida"] == 25.0


def test_empty_classified_products():
    df = pd.DataFrame({
        "Código do Produto": ["P1"],
        "Produto": ["X"],
        "Venda (R$)": [0.0],
        "Margem Atual": [10.0],
        "ABC": ["N/A"],
    })
    result, wam, warning = optimize_margins(df, 2.0, MAX_INCREASES)
    assert warning is not None
    assert result["Margem Sugerida"].iloc[0] == 10.0
