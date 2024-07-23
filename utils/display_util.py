# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: simple introduction of the code
import datetime
from typing import Dict

import pandas as pd

from transaction import Transaction, Repo
from utils.db_util import Constants as C
from utils.market_util import MarketUtil
from utils.txn_factory import TxnFactory


# 将数据处理后显示到web页面上
class DisplayUtil:

    def __init__(self, txn: Transaction) -> None:
        self.txn = txn

    def daily_data(self) -> pd.DataFrame:

        daily = self.txn.daily_data(self.txn.start_time, self.txn.end_time, self.txn.direction)
        # print(daily[C.TRADE_AMT].sum())
        market_irt = MarketUtil().get_irt(self.txn.start_time, self.txn.end_time)

        if market_irt.empty:
            return daily
        else:
            return pd.merge(daily, market_irt, left_on=C.AS_DT, right_on=C.DATE, how='left')

    def party_rank(self) -> pd.DataFrame:

        return self.txn.party_rank()

    def party_rank_n(self, n: int = 10) -> pd.DataFrame:

        raw = self.party_rank()

        if raw.empty:
            return raw

        df = raw.copy()
        # 保留日均余额前n位交易对手，超过n位归入到"其他"
        nums = len(df)

        if nums <= n:
            return df
        else:
            # 保留日均余额前n位交易对手，超过n位归入到"其他"
            tail = df.tail(nums - n)
            data = {
                C.NAME: ['其他'],
                C.AVG_AMT: [tail[C.AVG_AMT].sum()],
                C.INST_GROUP: [tail[C.INST_GROUP].sum()],
                C.PRODUCT: [tail[C.PRODUCT].sum()],
                C.WEIGHT_RATE: [tail[C.INST_GROUP].sum() * 365 / tail[C.PRODUCT].sum() * 100]
            }
            lastn = pd.DataFrame(data)

            df.drop(df.tail(nums - n).index, inplace=True)
            df = pd.concat([df, lastn]).reset_index(drop=True)

            return df

    def add_total(self, raw: pd.DataFrame, flag: int = 1) -> pd.DataFrame:
        # flag为1时，合计在最后，为0时，合计在最前

        if raw.empty:
            return raw

        df = raw.copy()
        rate_total = df[C.INST_GROUP].sum() * self.txn.inst_base / df[C.PRODUCT].sum() * 100 \
            if df[C.PRODUCT].sum() != 0 else 0

        total = {
            df.columns[0]: '合计',
            C.AVG_AMT: df[C.AVG_AMT].sum(),
            C.INST_GROUP: df[C.INST_GROUP].sum(),
            C.PRODUCT: df[C.PRODUCT].sum(),
            C.WEIGHT_RATE: rate_total
        }
        if flag == 1:
            return pd.concat([df, pd.DataFrame([total])]).reset_index(drop=True)
        else:
            return pd.concat([pd.DataFrame([total]), df]).reset_index(drop=True)

    def term_rank(self) -> pd.DataFrame:

        return self.txn.term_rank()

    def occ_stats(self) -> Dict:

        return self.txn.occ_stats()

    @staticmethod
    def format_output(raw: pd.DataFrame) -> pd.DataFrame:
        raw.index = raw.index + 1
        raw[C.AVG_AMT] = raw[C.AVG_AMT].map('{:,.2f}'.format)
        raw[C.INST_GROUP] = raw[C.INST_GROUP].map('{:,.2f}'.format)
        raw[C.WEIGHT_RATE] = raw[C.WEIGHT_RATE].map('{:.4f}'.format)

        return raw


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)

    d = DisplayUtil(TxnFactory(Repo).create_txn(s_t, e_t, "正回购"))
    print(d.daily_data())
