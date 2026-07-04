import pandas as pd
import numpy as np


def clean_column_names(df):
    """
    Column names to lowercase, replace spaces with "_"
    """
    df = df.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df

def drop_blank_order_dates(df):
    # Drop NaNs
    df = df[df['order_date'].notna()]
    # Drop empty or whitespace-only strings
    return df[df['order_date'].str.strip() != '']


def fill_missing_with_zero(df, column_name):
    """
    Replace NaN values in the specified column with 0.
    """
    df = df.copy()
    df[column_name] = df[column_name].fillna(0)
    return df

