import dataclasses
import json

@dataclasses.dataclass
class Currency:
    cc:str
    symbol: str
    name: str

def _get_currencies():
    with open('/home/valeriaps/PluggyTests/src/financial_assets/currencies.json') as f:
        json.load(f)
    return json.loads('/home/valeriaps/PluggyTests/src/financial_assets/currencies.json')
