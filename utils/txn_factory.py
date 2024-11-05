# Author: RockMan
# CreateTime: 2024/7/23
# FileName: tx_factory
# Description: This module contains a factory class for creating transaction objects.

import datetime
from typing import Type

from fund_tx import FundTx, Repo, IBO


class FundTxFactory:
    """
    资金交易的工厂类.

    Args:
        txn_factory: 创建对象类型.
    """

    def __init__(self, txn_factory: Type[FundTx]) -> None:
        """
        构造函数

        Args:
            txn_factory (Type[FundTx]): 被创建对象类型.
        """

        self.tx_factory = txn_factory

    def create_txn(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> FundTx:
        """
        创建一个具体的资金交易类.

        Args:
            start_time (datetime.date): 统计开始时间
            end_time (datetime.date): 统计结束时间
            direction (str): 交易方向

        Returns:
            FundTx: 资金交易类.
        """

        txn = self.tx_factory(start_time, end_time, direction)
        return txn


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)
    repo = FundTxFactory(Repo).create_txn(s_t, e_t, "正回购")
    ibo = FundTxFactory(IBO).create_txn(s_t, e_t, "拆借")
