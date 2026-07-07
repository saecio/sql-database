import pandas as pd
import numpy as np

def clean_column_names(df):
    """
    Normalize column names:
    - Convert to lowercase
    - Replace spaces with underscores
    Example: 'Order Date' becomes 'order_date'
    """
    df = df.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df

def drop_blank_order_dates(df):
    """
    Remove rows where order_date is missing or empty.
    These represent ~1% of rows and cannot be used for time-based analysis.
    """
    df = df[df['order_date'].notna()]
    return df[df['order_date'].str.strip() != '']

def fill_missing_with_zero(df, column_name):
    """
    Replace NaN values in the specified column with 0.
    Used for numeric columns where missing means no value (e.g. discount_pct).
    """
    df = df.copy()
    df[column_name] = df[column_name].fillna(0)
    return df

def create_price_columns(df):
    """
    Rename existing price/amount columns and calculate price per box
    before discount was applied.
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

def create_amount_columns_without_total(df):
    """
    Calculate order amounts before and after discount.
    Negative values are kept as they represent product returns.
    """
    df = df.copy()
    df["amount_before_discount"] = (
        df["price_per_box_before_discount"] * df["boxes_shipped"]
    ).round(2)
    df["amount_after_discount"] = (
        df["price_per_box_after_discount"] * df["boxes_shipped"]
    ).round(2)
    return df

def compute_total_discount(df):
    """
    Compute the total discount amount per order.
    total_discount = amount_before_discount - amount_after_discount
    """
    df = df.copy()
    df["total_discount"] = (
        df["amount_before_discount"] - df["amount_after_discount"]
    ).round(2)
    return df

def split_into_tables(df):
    """
    Normalize the cleaned DataFrame into 3 tables for the relational database:
    - products:     one row per unique product, with a generated product_id (PK)
    - salespersons: one row per unique salesperson, with a generated salesperson_id (PK)
    - invoices:     one row per order, with foreign keys to products and salespersons
    Returns a tuple: (products, salespersons, invoices)
    """
    df = df.copy()

    # Extract unique products and assign a numeric ID as primary key
    products = (
        df[["product"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    products.insert(0, "product_id", products.index + 1)

    # Extract unique salespersons and assign a numeric ID as primary key
    salespersons = (
        df[["salesperson"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    salespersons.insert(0, "salesperson_id", salespersons.index + 1)

    # Replace name columns with foreign key IDs
    invoices = df.merge(products, on="product", how="left")
    invoices = invoices.merge(salespersons, on="salesperson", how="left")
    invoices = invoices.drop(columns=["product", "salesperson", "amount_deprecated"])

    # Move foreign keys just after the first column for readability
    cols = invoices.columns.tolist()
    fk_cols = ["product_id", "salesperson_id"]
    other_cols = [c for c in cols if c not in fk_cols]
    invoices = invoices[other_cols[:1] + fk_cols + other_cols[1:]]

    return products, salespersons, invoices

import os

print("Répertoire courant :", os.getcwd())

def export_tables(products, salespersons, invoices, output_dir="data/clean"):
    """
    Export the 3 normalized tables to CSV files ready for MySQL import.
    MySQL import order:
      1. products.csv       (no foreign keys)
      2. salespersons.csv   (no foreign keys)
      3. invoices.csv       (references products and salespersons)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    products.to_csv(f"{output_dir}/products.csv", index=False)
    salespersons.to_csv(f"{output_dir}/salespersons.csv", index=False)
    invoices.to_csv(f"{output_dir}/invoices.csv", index=False)
    print(f"products.csv — {len(products)} rows")
    print(f"salespersons.csv — {len(salespersons)} rows")
    print(f"invoices.csv — {len(invoices)} rows")
    print(f"Files saved to: {output_dir}/")