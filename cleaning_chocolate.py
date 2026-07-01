import pandas as pd
import numpy as np

def clean_column_names(df):
    """
    Column names to lowercase, replace spaces with "_"
    """
    df = df.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    return df