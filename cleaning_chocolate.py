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

def create_amount_columns_without_total(df):
    """
    Calculate order amounts before and after discount, but NOT total_discount.
    Negative shipped boxes are retained as returns, producing negative amounts.
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
    Compute total_discount from amount_before_discount and amount_after_discount.
    Assumes those columns are already present and (optionally) imputed.
    """
    df = df.copy()

    df["total_discount"] = (
        df["amount_before_discount"] - df["amount_after_discount"]
    ).round(2)

    return df
    
def impute_missing_by_group(df, columns, group_col="product"):
    """
    Fill missing values in `columns` with the median of their group
    (defined by group_col). Used to impute price/amount gaps per product
    before computing total_discount.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df.groupby(group_col)[col].transform(lambda x: x.fillna(x.median()))
    return df


def convert_order_date_dtype(df):
    """
    Convert order_date from string to datetime, so it exports as a proper
    DATE type for MySQL rather than text. Dates are in mixed formats, so we use format="mixed" to handle both "YYYY-MM-DD" and "MM/DD/YYYY" formats.
    """
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed", dayfirst=False)
    return df


def compute_product_price_stats(df):
    """
    Descriptive price stats per product from price_per_box_before_discount.
    Used to inspect the original algebraically-derived prices before they
    are overridden with market-standard reference values.
    """
    return (
        df.groupby("product")["price_per_box_before_discount"]
        .agg(["median", "mean", "min", "max", "std", "count"])
        .round(2)
        .reset_index()
    )


def build_products_table(df, price_mapping):
    """
    Build the products table: one row per product, surrogate product_id,
    and a market-standard reference price from price_mapping (since the
    original price_per_box was confirmed to be randomly generated).
    """
    products = compute_product_price_stats(df)
    products["price"] = products["product"].map(price_mapping)
    products.insert(0, "product_id", range(1, len(products) + 1))
    return products[["product_id", "product", "price"]]


def build_salespersons_table(df):
    """
    Build the salespersons table: one row per unique salesperson,
    with a surrogate salesperson_id.
    """
    salespersons = df[["salesperson"]].drop_duplicates().reset_index(drop=True)
    salespersons.insert(0, "salesperson_id", range(1, len(salespersons) + 1))
    return salespersons[["salesperson_id", "salesperson"]]


def build_invoices_table(df, products, salespersons):
    """
    Build the invoices table. Price/amount columns are recalculated from
    the market-standard product price (not the original price_per_box),
    since that field was confirmed to be randomly generated.
    """
    invoices = df.copy()

    invoices = invoices.merge(products[["product_id", "product", "price"]], on="product", how="left")
    invoices = invoices.merge(salespersons[["salesperson_id", "salesperson"]], on="salesperson", how="left")

    invoices["price_per_box_before_discount"] = invoices["price"].round(2)
    invoices["price_per_box_after_discount"] = (
        invoices["price_per_box_before_discount"] * (1 - invoices["discount_pct"] / 100)
    ).round(2)
    invoices["amount_before_discount"] = (
        invoices["price_per_box_before_discount"] * invoices["boxes_shipped"]
    ).round(2)
    invoices["amount_after_discount"] = (
        invoices["price_per_box_after_discount"] * invoices["boxes_shipped"]
    ).round(2)
    invoices["total_discount"] = (
        invoices["amount_before_discount"] - invoices["amount_after_discount"]
    ).round(2)

    drop_cols = [c for c in ["product", "salesperson", "price", "amount_deprecated"] if c in invoices.columns]
    invoices = invoices.drop(columns=drop_cols)

    cols = [
        "order_id", "product_id", "salesperson_id", "country", "channel",
        "order_date", "discount_pct", "marketing_spend", "boxes_shipped",
        "price_per_box_before_discount", "price_per_box_after_discount",
        "amount_before_discount", "amount_after_discount", "total_discount",
    ]
    return invoices[cols]
    
import os

print("Répertoire courant :", os.getcwd())

def export_tables(products, salespersons, invoices, output_dir="data/clean"):
    """
    Export the 3 tables to CSV files in the given output directory.
    Import order for MySQL:
      1. products.csv       (no foreign keys)
      2. salespersons.csv   (no foreign keys)
      3. invoices.csv       (references both tables above)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    products.to_csv(f"{output_dir}/products.csv", index=False)
    salespersons.to_csv(f"{output_dir}/salespersons.csv", index=False)
    invoices.to_csv(f"{output_dir}/invoices.csv", index=False)

    print(f"products.csv     — {len(products)} rows")
    print(f"salespersons.csv — {len(salespersons)} rows")
    print(f"invoices.csv     — {len(invoices)} rows")
    print(f"Files saved to: {output_dir}/")
    
