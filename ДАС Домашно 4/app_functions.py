from datetime import datetime
import pandas as pd
from typing import Union, Optional


class DataCleaner:
    """Utility class for cleaning and formatting data values."""

    @staticmethod
    def clean_date(date_value: Union[str, int]) -> str:

        try:
            date_str = str(date_value).strip()

            # If already in correct format, return as is
            if len(date_str) == 10 and date_str[2] == '.' and date_str[5] == '.':
                return date_str

            # Handle numeric date strings (e.g., "8112024" or "08112024")
            if date_str.isdigit() and len(date_str) in [7, 8]:
                if len(date_str) == 7:
                    date_str = '0' + date_str

                day = date_str[:2]
                month = date_str[2:4]
                year = date_str[4:]

                # Validate date components
                datetime(int(year), int(month), int(day))

                return f"{day}.{month}.{year}"

            raise ValueError(f"Invalid date format: {date_value}")

        except (ValueError, IndexError) as e:
            # Log error here if needed
            return str(date_value)

    @staticmethod
    def clean_numeric(value: Union[str, float, int, None]) -> float:

        if pd.isna(value) or value == "":
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                # Remove whitespace and handle common number formats
                cleaned = value.strip().replace(" ", "")

                # Handle European number format (1.234,56 -> 1234.56)
                if "." in cleaned and "," in cleaned:
                    if cleaned.index(".") < cleaned.index(","):
                        cleaned = cleaned.replace(".", "").replace(",", ".")

                # Handle simple comma as decimal separator
                cleaned = cleaned.replace(",", ".")

                return float(cleaned)

            except (ValueError, AttributeError) as e:
                # Log error here if needed
                return 0.0

        return 0.0

    @classmethod
    def clean_dataframe(cls, df: pd.DataFrame,
                        numeric_columns: Optional[list] = None,
                        date_columns: Optional[list] = None) -> pd.DataFrame:

        df = df.copy()

        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].apply(cls.clean_numeric)

        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].apply(cls.clean_date)

        return df


# Function aliases for backward compatibility
clean_date = DataCleaner.clean_date
clean_numeric = DataCleaner.clean_numeric