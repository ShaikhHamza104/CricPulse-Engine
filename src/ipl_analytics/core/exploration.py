import pandas as pd
from pathlib import Path
from ipl_analytics.core.utils import read_parquet_file

def explore_data(
    data: pd.DataFrame | str | Path,
    sample_rows: int = 5,
) -> dict[str, object]:
    """
    Create a complete data-exploration report.

    The report includes:
    - Dataset shape
    - Column data types
    - Missing values
    - Duplicate rows
    - Numeric statistics
    - Categorical statistics
    - Sample rows
    """
    if sample_rows < 0:
        raise ValueError("sample_rows must be greater than or equal to zero")

    if isinstance(data, (str, Path)):
        df = read_parquet_file(Path(data))
    else:
        df = data
    # Lower case all column names for consistency
    df.columns = df.columns.str.lower()
    # lower case all string columns for consistency
    str_cols = df.select_dtypes(include=["object", "string"])
    for col in str_cols.columns:
        df[col] = df[col].str.lower()
    missing_values = (
        df.isna()
        .sum()
        .rename("missing_count")
        .to_frame()
    )
    missing_values["missing_percentage"] = (
        (missing_values["missing_count"] / len(df) * 100)
        if len(df) > 0
        else 0.0
    )

    column_details = pd.DataFrame(
        {
            "column": df.columns,
            "data_type": df.dtypes.astype(str).values,
            "non_null_count": df.notna().sum().values,
            "missing_count": df.isna().sum().values,
            "unique_count": df.nunique(dropna=True).values,
        }
    )
    numeric_cols = df.select_dtypes(include="number")
    numeric_summary = (
        numeric_cols.describe().T if not numeric_cols.columns.empty else pd.DataFrame()
    )
    categorical_cols = df.select_dtypes(include=["object", "category", "string"])
    categorical_summary = (
        categorical_cols.describe().T if not categorical_cols.columns.empty else pd.DataFrame()
    )

    return {
        "shape": df.shape,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / 1024**2,
            2,
        ),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_details": column_details,
        "missing_values": missing_values,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "sample": df.head(sample_rows),
    }