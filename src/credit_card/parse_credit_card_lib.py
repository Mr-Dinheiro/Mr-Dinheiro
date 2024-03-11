import pandas as pd
import zoneinfo
import credit_card.primitives as primitives
import json

def get_credit_card_transactions(file_path: str):
    df = pd.read_csv(file_path)
    df['date'] = df['date'].astype(pd.DatetimeTZDtype(tz=zoneinfo.ZoneInfo('Etc/GMT-3')))
    df['category'] = df['category'].astype(pd.CategoricalDtype())
    df['title'] = df['title'].astype(pd.StringDtype())
    df['amount'] = df['amount'].astype(pd.Float64Dtype())
    return df

def get_credit_card_info(file_path: str) -> primitives.CreditCardInfo:
    res = json.loads(file_path)
    print(res)

def get_transaction_categories(df: pd.DataFrame) -> set:
    return df['category'].cat.categories

def add_new_category(df: pd.DataFrame, new_category: str) -> None:
    if new_category in df['category'].cat.categories: return
    df['category'] = df['category'].cat.add_categories(new_category)

def get_transactions_per_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    return df.loc[df['category'] == category]

def batch_update_category(df: pd.DataFrame, from_category: str, to_category:str) -> None:
    """Changes the category from all transactions with from_category."""
    add_new_category(df, to_category)
    return df.mask(df == from_category, to_category)

def date_to_transaction_month(date: pd.Timestamp):
    return primitives.TransactionMonth(date.date().year, date.date().month)

def add_purchase_month_column(df: pd.DataFrame):
    ts = pd.Series(date_to_transaction_month(df['date']))
    df.insert(2, 'purchase_month', ts)

def get_total_by(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    return df.groupby(column_name)['amount'].agg(sum)
