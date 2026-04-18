import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pandas as pd
import pytest
from services.abc_classifier import classify_abc


def make_df(sales: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "Código do Produto": [f"P{i:03d}" for i in range(len(sales))],
        "Produto": [f"Produto {i}" for i in range(len(sales))],
        "Venda (R$)": sales,
        "Margem Atual": [20.0] * len(sales),
    })


def test_single_product_is_aplus():
    df = make_df([1000.0])
    result = classify_abc(df)
    assert result["ABC"].iloc[0] == "A+"


def test_zero_sales_tagged_na():
    df = make_df([0.0, 0.0])
    result = classify_abc(df)
    assert (result["ABC"] == "N/A").all()


def test_mixed_zero_and_nonzero():
    df = make_df([500.0, 0.0, 300.0])
    result = classify_abc(df)
    assert "N/A" in result["ABC"].values
    assert "A+" in result["ABC"].values or "A" in result["ABC"].values


def test_four_equal_products_cover_all_classes():
    """With equal sales, the first product covers 25% → A+, then subsequent push into A, B, C."""
    sales = [100.0] * 10
    df = make_df(sales)
    result = classify_abc(df)
    classes = set(result["ABC"].values)
    assert "A+" in classes
    assert "A" in classes


def test_abc_thresholds_known_data():
    """
    Total = 1000. Products sorted desc:
    P0=400 → cum=40% → A+
    P1=400 → cum=80% → A
    P2=150 → cum=95% → B
    P3=50  → cum=100% → C
    """
    df = pd.DataFrame({
        "Código do Produto": ["P0", "P1", "P2", "P3"],
        "Produto": ["A", "B", "C", "D"],
        "Venda (R$)": [400.0, 400.0, 150.0, 50.0],
        "Margem Atual": [20.0, 18.0, 15.0, 10.0],
    })
    result = classify_abc(df)
    abc_map = dict(zip(result["Código do Produto"], result["ABC"]))
    assert abc_map["P0"] == "A+"
    assert abc_map["P1"] == "A"
    assert abc_map["P2"] == "B"
    assert abc_map["P3"] == "C"


def test_preserves_original_row_order():
    df = make_df([50.0, 400.0, 150.0, 400.0])
    result = classify_abc(df)
    assert list(result.index) == list(df.index)


def test_all_products_receive_abc_column():
    df = make_df([100.0, 200.0, 300.0])
    result = classify_abc(df)
    assert "ABC" in result.columns
    assert result["ABC"].notna().all()
