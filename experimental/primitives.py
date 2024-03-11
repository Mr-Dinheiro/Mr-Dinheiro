import dataclasses
import validators

class CreditCardName:
    def __init__(self, name: int):
        validators.name_validator(name)
        self.name = name

class PossibleDueDate:

    def __init__(self, date: int):
        validators.possible_due_date_validator(date)
        self.due_date = date

@dataclasses.dataclass
class TransactionMonth:
    year: int
    month: int

    def __repr__(self) -> str:
        return f'{self.year}/{self.month}'

    def __hash__(self):
        return hash(self.year*100 + self.month)

    def __eq__(self, other):
        return self.year == other.year and self.month == other.month

    def __gt__(self, other):
        if self.year > other.year: return True
        if self.month > other.month: return True
        return False

@dataclasses.dataclass
class CreditCardInfo:
    name: CreditCardName
    due_date: PossibleDueDate
    closing_date: PossibleDueDate
