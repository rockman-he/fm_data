# Author: RockMan
# CreateTime: 2024/7/23
# FileName: txn_factory
# Description: simple introduction of the code
import datetime
from typing import Type

from transaction import Transaction, Repo, IBO


class TxnFactory:

    def __init__(self, txn_factory: Type[Transaction]) -> None:
        self.txn_factory = txn_factory

    def create_txn(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> Transaction:
        txn = self.txn_factory(start_time, end_time, direction)
        return txn


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)
    repo = TxnFactory(Repo).create_txn(s_t, e_t, "正回购")
    # print(repo.get_raw_test())
    #
    # ibo = TxnFactory(IBO).create_txn(s_t, e_t, "同业拆入")
    # print(ibo.get_raw_test())
