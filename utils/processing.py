# utils/processing.py

import polars as pl
import pandas as pd
from itertools import chain
import streamlit as st

@st.cache_data
def hourly_df_with_polars(df: pd.DataFrame, gas_col: str, timeframe: str, certain_year: int | None = None) -> pd.DataFrame:
    #df['Hour'] = df['Hour'].apply(lambda x: x.strftime('%H:%M:%S'))
    pl_df = pl.from_pandas(df).with_columns([
        pl.col("year").cast(pl.Int32),
        pl.col("municipality").cast(pl.Utf8),
        pl.col(gas_col).cast(pl.Float64)
    ])
    if pl_df["Hour"].dtype != pl.Utf8:
        pl_df = pl_df.with_columns([
            pl.col("Hour").dt.hour().cast(str).str.zfill(2).str.concat(":00:00").alias("Hour")
        ])
    else:
        pl_df = pl_df.with_columns([
            pl.col("Hour").str.strip_chars().str.zfill(8)
        ])

    if timeframe == "Certain year hours" and certain_year is not None:
        pl_df = pl_df.filter(pl.col("year") == certain_year)
    elif timeframe == "Last five years hours":
        last_five = sorted(pl_df["year"].unique().to_list())[-5:]
        pl_df = pl_df.filter(pl.col("year").is_in(last_five))

    pl_agg = pl_df.group_by(["municipality", "Hour"]).agg([
        pl.col(gas_col).mean().alias(gas_col)
    ])

    #all_years = pl_agg.select("year").unique()
    all_hours = pl.DataFrame({"Hour": [f"{h:02d}:00:00" for h in range(24)]})
    all_municipalities = pl_df.select("municipality").unique()
    full_grid = all_municipalities.join(all_hours, how="cross")

    full_df = full_grid.join(pl_agg, on=["municipality", "Hour"], how="left").with_columns([
        pl.col(gas_col).fill_null(-1)
    ])

    return full_df.sort(["municipality", "Hour"]).to_pandas()

@st.cache_data
def yearly_df_with_polars_from_raw(df: pd.DataFrame, gas_col: str) -> pd.DataFrame:
    pl_df = pl.from_pandas(df).with_columns([
        pl.col("year").cast(pl.Int32),
        pl.col("municipality").cast(pl.Utf8),
        pl.col(gas_col).cast(pl.Float64)
    ])

    pl_agg = pl_df.group_by(["municipality", "year"]).agg([
        pl.col(gas_col).mean().alias(gas_col)
    ])

    all_years = pl_df.select("year").unique()
    all_municipalities = pl_df.select("municipality").unique()
    full_grid = all_years.join(all_municipalities, how="cross")

    full_df = full_grid.join(pl_agg, on=["municipality", "year"], how="left").with_columns([
        pl.col(gas_col).fill_null(-1),
        pl.col("year").cast(str)
    ])

    return full_df.sort(["municipality", "year"]).to_pandas()

def has_stepsize_one(it):
    return all(x2 - x1 == 1 for x1, x2 in zip(it[:-1], it[1:]))

def get_values(dictionary, keys):
    if not isinstance(keys, (list, tuple)):  # Ensure keys are iterable
        keys = [keys]
    return list(chain.from_iterable(map(dictionary.get, keys)))
# ==for the fuel check==
def check_prefecture():
    # If 'Line Graph' is checked, uncheck 'Bar Chart'
    if st.session_state.prefecture_checked:
        st.session_state.region_checked = False

def check_region():
    # If 'Bar Chart' is checked, uncheck 'Line Graph'
    if st.session_state.region_checked:
        st.session_state.prefecture_checked = False