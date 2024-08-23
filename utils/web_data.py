# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: This module contains the WebDataHandler class
# which provides methods for displaying transaction data on a web page.
import datetime
from typing import Dict

import pandas as pd

from fund_tx import FundTx, Repo
from utils.db_util import Constants as C
from utils.market_util import MarketUtil
from utils.txn_factory import TxFactory


# 将数据处理后显示到web页面上
class WebDataHandler:
    """
    A utility class for displaying transaction data on a web page.

    Attributes:
        tx (FundTx): The transaction to display.
    """

    def __init__(self, txn: FundTx) -> None:
        """
        Initialize a WebDataHandler instance.

        Args:
            txn (FundTx): The transaction to datas.
        """

        self.tx = txn

    def daily_data(self) -> pd.DataFrame:
        """
        Retrieve holded data for the transaction and merge it with the Interbank Rate Table (IRT).

        Returns:
            pd.DataFrame: The holded data for the transaction merged with the IRT.
        """

        daily = self.tx.daily_data(self.tx.start_time, self.tx.end_time, self.tx.direction)
        market_irt = MarketUtil().get_irt(self.tx.start_time, self.tx.end_time)

        if market_irt.empty:
            return daily
        else:
            return pd.merge(daily, market_irt, left_on=C.AS_DT, right_on=C.DATE, how='left')

    def party_rank(self) -> pd.DataFrame:
        """
        Rank counterparties based on the transaction data.

        Returns:
            pd.DataFrame: The counterparty rankings.
        """

        return self.tx.party_rank()

    def party_rank_n(self, n: int = 10) -> pd.DataFrame:
        """
        Rank the top n counterparties based on the transaction data.

        Args:
            n (int): The number of top counterparties to rank, the default value is 10.

        Returns:
            pd.DataFrame: The top n counterparty rankings.
        """

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
        """
        Add a "total" row to the DataFrame.

        Args:
            raw (pd.DataFrame): The DataFrame to add the total row to.
            flag (int): If 1, add the total row at the end. If 0, add the total row at the beginning.

        Returns:
            pd.DataFrame: The DataFrame with the total row added.
        """

        # flag为1时，合计在最后，为0时，合计在最前

        if raw.empty:
            return raw

        df = raw.copy()
        rate_total = df[C.INST_GROUP].sum() * self.tx.inst_base / df[C.PRODUCT].sum() * 100 \
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
        """
        Rank terms based on the transaction data.

        Returns:
            pd.DataFrame: The term rankings.
        """

        return self.tx.term_rank()

    def occ_stats(self) -> Dict:
        """
        Calculate statistics for the transaction.

        Returns:
            Dict: The calculated statistics.
        """

        return self.tx.occ_stats()

    @staticmethod
    def format_output(raw: pd.DataFrame) -> pd.DataFrame:
        """
        Format the output DataFrame.
        1. Add 1 to the index.
        2. Format the average amount, interbank rate, and weighted rate columns.

        Args:
            raw (pd.DataFrame): The DataFrame to format.

        Returns:
            pd.DataFrame: The formatted DataFrame.
        """

        raw.index = raw.index + 1
        raw[C.AVG_AMT] = raw[C.AVG_AMT].map('{:,.2f}'.format)
        raw[C.INST_GROUP] = raw[C.INST_GROUP].map('{:,.2f}'.format)
        raw[C.WEIGHT_RATE] = raw[C.WEIGHT_RATE].map('{:.4f}'.format)

        return raw

    def get_txn_header(self) -> Dict:
        """
        Get the transaction header.

        This method retrieves various transaction data and statistics, including holded data, party rankings,
        term rankings, and occurrence statistics.
        It then packages these data into a dictionary and returns it.

        The returned dictionary has the following structure:
        - 'holded': The holded data for the transaction.
        - 'party': The counterparty rankings.
        - 'party_total': The counterparty rankings with a total row added at the end.
        - 'party_n': The top n counterparty rankings.
        - 'partyn_total': The top n counterparty rankings with a total row added at the beginning.
        - 'term': The term rankings.
        - 'term_total': The term rankings with a total row added at the end.
        - 'occ': The occurrence statistics.

        Returns:
            Dict: The transaction header.
        """

        txn_daily = self.daily_data()
        txn_party = self.party_rank()
        txn_party_total = self.add_total(txn_party, 1)
        txn_party_n = self.party_rank_n()
        txn_partyn_total = self.add_total(txn_party_n, 0)
        txn_term = self.term_rank()
        txn_term_total = self.add_total(txn_term, 1)
        txn_occ = self.occ_stats()

        return {
            'holded': txn_daily,
            'party': txn_party,
            'party_total': txn_party_total,
            'party_n': txn_party_n,
            'partyn_total': txn_partyn_total,
            'term': txn_term,
            'term_total': txn_term_total,
            'occ': txn_occ

        }


if __name__ == "__main__":
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 12, 31)

    d = WebDataHandler(TxFactory(Repo).create_txn(s_t, e_t, "正回购"))
    print(d.daily_data())