import pandas as pd


class PluggyDataHandler:
    def save_transactions_as(
        self,
        transactions,
        file_path="transactions",
        format="csv",
    ):
        obfuscated_transactions = self.obfuscate_transactions(transactions)

        df = pd.DataFrame(obfuscated_transactions)
        if format == "csv":
            df.to_csv(f"{file_path}.csv", index=False)
        elif format == "jsonl":
            df.to_json(f"{file_path}.jsonl", orient="records", lines=True)
        else:
            raise ValueError("Invalid format. Use 'csv' or 'jsonl'")

    def obfuscate_field(self, data, field):
        if field in data:
            data[field] = self.obfuscate(data[field])

    def obfuscate_transactions(self, transactions):
        for transaction in transactions:
            self.obfuscate_field(transaction, "id")
            self.obfuscate_field(transaction, "accountId")

            credit_card_meta_data = transaction.get("creditCardMetadata")
            if credit_card_meta_data:
                self.obfuscate_field(credit_card_meta_data, "cardNumber")
                self.obfuscate_field(credit_card_meta_data, "payeeMCC")

            merchant_info = transaction.get("merchant")
            if merchant_info:
                self.obfuscate_field(merchant_info, "cnae")
                self.obfuscate_field(merchant_info, "cnpj")

        return transactions

    def obfuscate(self, field):
        obfuscation_functions = {
            int: lambda x: int("".join("0" if ch.isalnum() else ch for ch in str(x))),
            float: lambda x: float(
                "".join("0" if ch.isalnum() else ch for ch in str(x))
            ),
            str: lambda x: "".join("0" if ch.isalnum() else ch for ch in x),
        }

        obfuscate_func = obfuscation_functions.get(type(field))
        if obfuscate_func is None:
            raise ValueError(
                f"Obfuscation for type {type(field).__name__} is not supported"
            )
        return obfuscate_func(field)
