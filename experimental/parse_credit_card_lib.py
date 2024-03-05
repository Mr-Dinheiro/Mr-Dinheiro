import pandas as pd
import zoneinfo
import dataclasses

@dataclasses.dataclass
class AccrualMonth:
    year: int
    month: int

    # def __repr__(self):
    #     return f"{self.year}/{self.month}"
    def __hash__(self):
        return hash(self.year*100 + self.month)

    def __eq__(self, other):
        return self.year == other.year and self.month == other.month

def get_data(file_path: str):
    df = pd.read_csv(file_path)
    df['date'] = df['date'].astype(pd.DatetimeTZDtype(tz=zoneinfo.ZoneInfo('Etc/GMT-3')))
    df['category'] = df['category'].astype(pd.CategoricalDtype())
    df['title'] = df['title'].astype(pd.StringDtype())
    df['amount'] = df['amount'].astype(pd.Float64Dtype())
    return df

def get_transaction_categories(df: pd.DataFrame) -> set:
    return df['category'].cat.categories

def get_total_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby('category')['amount'].agg(sum)

def add_new_category(df: pd.DataFrame, new_category: str) -> None:
    if new_category in df['category'].cat.categories: return
    df['category'] = df['category'].cat.add_categories(new_category)

def get_transactions_per_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    return df.loc[df['category'] == category]

def batch_update_category(df: pd.DataFrame, from_category: str, to_category:str) -> None:
    """Changes the category from all transactions with from_category."""
    add_new_category(df, to_category)
    return df.mask(df == from_category, to_category)

def date_to_accrual_month(date: pd.Timestamp):
    return AccrualMonth(date.date().year, date.date().month)

def add_accrual_month_column(df: pd.DataFrame):
    ts = pd.Series(date_to_accrual_month(df['date']))
    df.insert(2, 'accrual_month', ts)


def get_total_by_accrual_month(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby('accrual_month')['amount'].agg(sum)