# Author: RockMan
# CreateTime: 2024/7/23
# FileName: tx_factory
# Description: This module contains a factory class for creating transaction objects.

import datetime
from typing import Type

from fund_tx import FundTx, Repo, IBO


class TxFactory:
    """
    A factory class for creating transaction objects.

    Args:
        txn_factory: The type of transaction to create.
    """

    def __init__(self, txn_factory: Type[FundTx]) -> None:
        """
        Initialize a TxFactory instance.

        Args:
            txn_factory (Type[FundTx]): The type of transaction to create.
        """

        self.tx_factory = txn_factory

    def create_txn(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> FundTx:
        """
        Create a transaction object.

        Args:
            start_time (datetime.date): The start time of the transaction.
            end_time (datetime.date): The end time of the transaction.
            direction (str): The direction of the transaction.

        Returns:
            FundTx: A transaction object.
        """

        txn = self.tx_factory(start_time, end_time, direction)
        return txn


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)
    repo = TxFactory(Repo).create_txn(s_t, e_t, "正回购")
    ibo = TxFactory(IBO).create_txn(s_t, e_t, "拆借")
