
_MAX_NAME_LEN = 60

def possible_due_date_validator(date: int):
    if not 1 < date < 28:
        raise ValueError("Due date must be between 1 and 28 inclusive.")
    

def name_validator(name: str):
    if len(name) > _MAX_NAME_LEN:
        raise ValueError(f"Name cannot be larger than {_MAX_NAME_LEN}.")
