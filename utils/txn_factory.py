# Author: RockMan
# CreateTime: 2024/7/23
# FileName: tx_factory
# Description: This module contains a factory class for creating transaction objects.

import datetime
from typing import Type, Union

from bond_tx import SecurityTx, BondTx
from fund_tx import FundTx, Repo, IBO


class TxFactory:
    """
    交易的工厂类.

    Args:
        txn_factory: 创建对象类型.
    """

    def __init__(self, txn_factory: Union[Type[FundTx], Type[SecurityTx]]) -> None:
        """
        构造函数

        Args:
            txn_factory (Union[Type[FundTx], Type[SecurityTx]]): 被创建对象类型.
        """

        self.tx_factory = txn_factory

    def create_txn(self, start_time: datetime.date, end_time: datetime.date) -> Union[FundTx, SecurityTx]:
        """
        创建一个具体的交易类.

        Args:
            start_time (datetime.date): 统计开始时间
            end_time (datetime.date): 统计结束时间

        Returns:
            Union[FundTx, SecurityTx]: 交易类.
        """

        txn = self.tx_factory(start_time, end_time)
        return txn


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)
    repo = TxFactory(Repo).create_txn(s_t, e_t)
    ibo = TxFactory(IBO).create_txn(s_t, e_t)

    bond = TxFactory(BondTx).create_txn(s_t, e_t)
