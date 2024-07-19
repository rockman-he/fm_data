# Author: RockMan
# CreateTime: 2024/7/15
# FileName: transaction
# Description: simple introduction of the code
import datetime
from abc import ABC, abstractmethod, ABCMeta

import pandas as pd
import streamlit as st

from utils.db_util import Constants as C, create_conn, get_raw


class Transaction(ABC, metaclass=ABCMeta):
    """
    This is an abstract base class for all repurchase and lending transactions.
    """

    def __init__(self, start_time, end_time, direction):
        """
        Initialize a Transaction instance.
        :param start_time:
        :param end_time:
        :param direction:
        """
        self.start_time = start_time
        self.end_time = end_time
        self.direction = direction
        self.raw = None

    @abstractmethod
    def _get_raw_data(self) -> pd.DataFrame:
        raise NotImplementedError

    # start_time, end_time, direciton仅为缓存的key
    @abstractmethod
    def daily_data(_self, start_time, end_time, direciton) -> pd.DataFrame:
        raise NotImplementedError

    # start_time, end_time, direciton仅为缓存的key
    @abstractmethod
    # 交易对手排名
    def party_rank(_self, start_time, end_time, direciton) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def term_type(_self, start_time, end_time, direciton) -> pd.DataFrame:
        raise NotImplementedError


class Repo(Transaction):

    def __init__(self, start_time, end_time, direction):
        super().__init__(start_time, end_time, direction)
        self.raw = self._get_raw_data()

    def _get_raw_data(self) -> pd.DataFrame:

        self.direction = '4' if self.direction == '正回购' else '1'
        sql = f"select tc.{C.TRADE_NO}, tc.{C.TERM_TYPE}, tc.{C.COUNTERPARTY}, bar.{C.MAIN_ORG}, " \
              f"tc.{C.DIRECTION}, tc.{C.REPO_RATE}, tc.{C.CONVERTED_BOND_AMOUNT}, tc.{C.BOND_AMOUNT}, " \
              f"tc.{C.REPO_AMOUNT}, tc.{C.INTEREST_AMOUNT}, tc.{C.SETTLEMENT_DATE}, tc.{C.MATURITY_DATE}, " \
              f"tc.{C.CASH_HOLDING_DAYS}, tc.{C.CHECK_STATUS}, tc.{C.TRADER} " \
              f"from upsrod.trade_colrepoes tc " \
              f"left join upsrod.basic_agencies_relation bar " \
              f"on tc.{C.COUNTERPARTY}  = bar.{C.SUB_ORG} " \
              f"where tc.{C.MATURITY_DATE} > '" + self.start_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.SETTLEMENT_DATE} <= '" + \
              self.end_time.strftime('%Y-%m-%d') + f"' and tc.{C.CHECK_STATUS} = 1 and " + \
              f"tc.{C.DIRECTION} = " + self.direction + \
              f" order by tc.{C.SETTLEMENT_DATE};"

        # 如果用户选择的截至时间晚于起始时间，则返回空df
        if self.start_time > self.end_time:
            return pd.DataFrame({})

        # 从数据库中获取数据
        raw = get_raw(create_conn(), sql)

        if raw.empty:
            return pd.DataFrame({})

        # 由于upsrod.basic_agencies_relation表中存在一个子机构对应多个主机构的情况，因此按C.TRADE_NO删除重复项，保留第一个出现的数据项
        raw.drop_duplicates(C.TRADE_NO, inplace=True)

        # 如果主机构为空，则用子机构的名称代替
        mask = raw[C.MAIN_ORG].isnull()
        raw.loc[mask, C.MAIN_ORG] = raw.loc[mask, C.COUNTERPARTY]

        # C.AS_DT: 实际统计开始时间， C.AE_DT： 实际统计结束时间
        # 增加两列，初始化
        raw[C.AS_DT] = raw[C.SETTLEMENT_DATE]
        raw[C.AE_DT] = raw[C.MATURITY_DATE]

        # 对于在统计区间，但是起止时间超出的部分做初始化处理，方便以后计算
        mask = raw[C.AS_DT] < pd.to_datetime(self.start_time)
        raw.loc[mask, C.AS_DT] = pd.to_datetime(self.start_time)

        # 注意：如果C.AE_DT（到期结算日） > end_time，那实际统计日当天也是要计算利息，对于该情况，要加上一天
        mask = raw[C.AE_DT] > pd.to_datetime(self.end_time)
        raw.loc[mask, C.AE_DT] = pd.to_datetime(self.end_time) + datetime.timedelta(days=1)

        # 统计区间的实际计息天数
        raw[C.WORK_DAYS] = (raw[C.AE_DT] - raw[C.AS_DT]).apply(lambda x: x.days)
        # 积数
        raw[C.PRODUCT] = raw[C.REPO_AMOUNT] * raw[C.WORK_DAYS]

        # 统计区间内实际收取的利息，C.INST_DAYS为区间总利息，C.INST_A_DAY为每天的利息
        raw[C.INST_DAYS] = (raw[C.INTEREST_AMOUNT] / raw[C.CASH_HOLDING_DAYS]
                            * raw[C.WORK_DAYS])
        raw[C.INST_A_DAY] = raw[C.INTEREST_AMOUNT] / raw[C.CASH_HOLDING_DAYS]

        return raw

    @st.cache_data()
    def daily_data(_self, start_time, end_time, direciton) -> pd.DataFrame:

        if _self.raw.empty:
            return pd.DataFrame({})

        date_range = pd.date_range(start=_self.start_time, end=_self.end_time, freq='D')
        repo = pd.DataFrame(date_range, columns=[C.AS_DT])
        repo[C.REPO_AMOUNT] = 0.0
        repo[C.INST_DAYS] = 0.0

        # 遍历数据库查询结果
        for row in _self.raw.index:
            # 回购金额
            repo_amt = _self.raw.loc[row][C.REPO_AMOUNT]
            # 满足统计区间的起始时间
            as_date = _self.raw.loc[row][C.AS_DT]
            # 满足统计区间的截至时间
            ae_date = _self.raw.loc[row][C.AE_DT]
            # 每天的利息
            inst_a_day = _self.raw.loc[row][C.INST_A_DAY]

            # 将起止时间段的回购余额和利息总额进行汇总
            mask = (repo[C.AS_DT] >= as_date) & (repo[C.AS_DT] < ae_date)
            repo.loc[mask, [C.REPO_AMOUNT]] += repo_amt
            repo.loc[mask, [C.INST_DAYS]] += inst_a_day

        repo[C.WEIGHT_RATE] = repo[C.INST_DAYS] * 365 / repo[C.REPO_AMOUNT] * 100
        repo[C.WEIGHT_RATE] = repo[C.WEIGHT_RATE].fillna(0)

        return repo

    @st.cache_data()
    def party_rank(_self, start_time, end_time, direciton) -> pd.DataFrame:

        if _self.raw.empty:
            return pd.DataFrame({})

        repo_rank = _self.groupby_column(C.MAIN_ORG)

        return repo_rank

    def term_type(_self, start_time, end_time, direciton) -> pd.DataFrame:

        if _self.raw.empty:
            return pd.DataFrame({})

        term_type = _self.groupby_column(C.TERM_TYPE)

        return term_type

    def groupby_column(self, column: str) -> pd.DataFrame:
        # 按期限类型进行分组
        repo_group = self.raw.groupby(self.raw[column])
        # 利息加总
        inst_group = repo_group[C.INST_DAYS].agg("sum")
        # 积数加总
        product = repo_group[C.PRODUCT].agg("sum")
        # 加权利率
        weight_rate = inst_group * 365 / product * 100
        # 计算日均余额
        avg_amt = product / ((self.end_time - self.start_time).days + 1)
        # 分组后按日均余额升序排列
        term_type = pd.DataFrame({C.AVG_AMT: avg_amt,
                                  C.INST_GROUP: inst_group,
                                  C.PRODUCT: product,
                                  C.WEIGHT_RATE: weight_rate})
        term_type.sort_values(by=C.AVG_AMT, ascending=False, inplace=True)
        term_type.reset_index(inplace=True)
        return term_type


if __name__ == '__main__':
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 6, 1)
    repo = Repo(s_t, e_t, '正回购')
    c = repo.party_rank(0, 0, 0)
    print(c)
