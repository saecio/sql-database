import pandas as pd
import numpy as np


def clean_column_names(df):
    """
    Column names to lowercase, replace spaces with "_"
    """
    df = df.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df


def create_price_columns(df):
    """
    Rename the existing price and amount columns and calculate the price
    per box before discount.
    """
    df = df.copy()

    df = df.rename(columns={
        "price_per_box": "price_per_box_after_discount",
        "amount": "amount_deprecated"
    })

    df["discount_pct"] = df["discount_pct"].fillna(0)
    discount_factor = 1 - df["discount_pct"] / 100

    df["price_per_box_before_discount"] = (
        df["price_per_box_after_discount"] / discount_factor
    )

    return df


def create_amount_columns(df):
    """
    Calculate order amounts before and after discount and the total discount.
    Negative shipped boxes are retained as returns, producing negative amounts.
    """
    df = df.copy()

    df["amount_before_discount"] = (
        df["price_per_box_before_discount"] * df["boxes_shipped"]
    ).round(2)

    df["amount_after_discount"] = (
        df["price_per_box_after_discount"] * df["boxes_shipped"]
    ).round(2)

    df["total_discount"] = (
        df["amount_before_discount"] - df["amount_after_discount"]
    ).round(2)

    return df
