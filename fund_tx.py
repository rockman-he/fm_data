# Author: RockMan
# CreateTime: 2024/7/15
# FileName: transaction
# Description: This module contains classes for handling transactions.
import datetime
from typing import Dict

import pandas as pd
import streamlit as st

from utils.db_util import Constants as C, create_conn, get_raw


class FundTx:
    """
    This is an abstract base class for repo and ibo transactions.

    Attributes:
        start_time (datetime.date): The start time of the transaction.
        end_time (datetime.date): The end time of the transaction.
        direction (str): The direction of the transaction.
        inst_base (int): The base for calculating interest.
        raw (pd.DataFrame): The raw data for the transaction.
    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> None:
        """
        Initialize a FundTx instance.

        Args:
            start_time (datetime.date): The start time of the transaction.
            end_time (datetime.date): The end time of the transaction.
            direction (str): The direction of the transaction.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.direction = direction
        self.inst_base = 365
        self.raw = None

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        Retrieve raw data from the database.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            pd.DataFrame: The raw data retrieved from the database.
        """

        # 如果用户选择的截至时间晚于起始时间，则返回空df
        if self.start_time > self.end_time:
            return pd.DataFrame({})

        # 从数据库中获取数据
        raw = get_raw(create_conn(), sql)

        if raw.empty:
            return pd.DataFrame({})

        # 由于upsrod.basic_agencies_relation表中存在一个子机构对应多个主机构的情况，因此按C.TRADE_NO删除重复项，保留第一个出现的数据项
        raw.drop_duplicates(C.TRADE_NO, inplace=True)

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
        # # 积数
        raw[C.PRODUCT] = raw[C.TRADE_AMT] * raw[C.WORK_DAYS]

        # 统计区间内实际收取的利息，C.INST_DAYS为区间总利息，C.INST_A_DAY为每天的利息
        raw[C.INST_DAYS] = (raw[C.INTEREST_AMT] / raw[C.HOLDING_DAYS]
                            * raw[C.WORK_DAYS])
        raw[C.INST_A_DAY] = raw[C.INTEREST_AMT] / raw[C.HOLDING_DAYS]

        return raw

    @st.cache_data
    # start_time, end_time, direciton仅为缓存机制用的key
    def daily_data(_self, start_time: datetime.date, end_time: datetime.date, direction: str) -> pd.DataFrame:
        """
        Retrieve holded data for the transaction.

        Args:
            start_time (datetime.date): The start time for retrieving the data.
            end_time (datetime.date): The end time for retrieving the data.
            direction (str): The direction of the transaction.

        Returns:
            pd.DataFrame: The holded data for the transaction.
        """

        # 仅仅是为了消除参数未用的警告
        start_time + datetime.timedelta(days=1)
        end_time + datetime.timedelta(days=1)
        len(direction)

        if _self.raw.empty:
            return pd.DataFrame({})

        date_range = pd.date_range(start=_self.start_time, end=_self.end_time, freq='D')
        daily = pd.DataFrame(date_range, columns=[C.AS_DT])
        daily[C.TRADE_AMT] = 0.0
        daily[C.INST_DAYS] = 0.0

        # 遍历数据库查询结果
        for row in _self.raw.index:
            # 回购金额
            trade_amt = _self.raw.loc[row][C.TRADE_AMT]
            # 满足统计区间的起始时间
            as_date = _self.raw.loc[row][C.AS_DT]
            # 满足统计区间的截至时间
            ae_date = _self.raw.loc[row][C.AE_DT]
            # 每天的利息
            inst_a_day = _self.raw.loc[row][C.INST_A_DAY]

            # 将起止时间段的回购余额和利息总额进行汇总
            mask = (daily[C.AS_DT] >= as_date) & (daily[C.AS_DT] < ae_date)
            daily.loc[mask, [C.TRADE_AMT]] += trade_amt
            daily.loc[mask, [C.INST_DAYS]] += inst_a_day

        daily[C.WEIGHT_RATE] = daily[C.INST_DAYS] * _self.inst_base / daily[C.TRADE_AMT] * 100
        daily[C.WEIGHT_RATE] = daily[C.WEIGHT_RATE].fillna(0)

        # print(daily.columns)

        return daily

    # 交易对手排名
    def party_rank(_self) -> pd.DataFrame:
        """
        Rank counterparties based on the transaction data.

        Returns:
            pd.DataFrame: The counterparty rankings.
        """

        if _self.raw.empty:
            return pd.DataFrame({})

        repo_rank = _self.__groupby_column(C.NAME)

        return repo_rank

    def term_rank(_self) -> pd.DataFrame:
        """
        Rank terms based on the transaction data.

        Returns:
            pd.DataFrame: The term rankings.
        """

        if _self.raw.empty:
            return pd.DataFrame({})

        return _self.__groupby_column(C.TERM_TYPE)

    def occ_stats(self) -> Dict:
        """
        Calculate statistics for the transaction.

        Returns:
            Dict: The calculated statistics.
        """

        if self.raw.empty:
            return {}

        mask = ((self.raw[C.SETTLEMENT_DATE] >= self.start_time.strftime('%Y-%m-%d')) &
                (self.raw[C.SETTLEMENT_DATE] <= self.end_time.strftime('%Y-%m-%d')))
        occ_stats = self.raw[mask]

        return {
            # 交易笔数
            C.TRADE_NUM: occ_stats.shape[0],
            # 交易总额（按发生）
            C.TRADE_SUM: occ_stats[C.TRADE_AMT].sum(),
            # 交易金额（按加权）
            C.TRADE_WEIGHT_SUM: self.raw[C.TRADE_AMT].sum(),
            # 单笔利率(最大）
            C.MAX_RATE: occ_stats[C.RATE].max(),
            # 单笔利率(最小）
            C.MIN_RATE: occ_stats[C.RATE].min()
        }

    def __groupby_column(self, column: str) -> pd.DataFrame:
        """
        Group the transaction data by a specific column.

        Args:
            column (str): The column to group by.

        Returns:
            pd.DataFrame: The grouped data.
        """

        # 按期限类型进行分组
        txn_group = self.raw.groupby(self.raw[column])
        # 利息加总
        inst_group = txn_group[C.INST_DAYS].agg("sum")
        # 积数加总
        product = txn_group[C.PRODUCT].agg("sum")
        # 加权利率
        weight_rate = inst_group * self.inst_base / product * 100
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

    def get_stime(self):
        return self.start_time

    def get_etime(self):
        return self.end_time

    def get_dierection(self):
        return self.direction


class Repo(FundTx):
    """
    This class represents a repo transaction.

    Attributes:
        start_time (datetime.date): The start time of the transaction.
        end_time (datetime.date): The end time of the transaction.
        direction (str): The direction of the transaction.
    """

    # TODO 还缺少买断式回购、交易所回购的统计，同时要补全机构的code
    def __init__(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> None:
        """
        Initialize a Repo instance.

        Args:
            start_time (datetime.date): The start time of the transaction.
            end_time (datetime.date): The end time of the transaction.
            direction (str): The direction of the transaction.
        """

        super().__init__(start_time, end_time, direction)

        self.direction = '4' if self.direction == '正回购' else '1'
        sql = f"select " \
              f"tc.{C.TRADE_NO}, " \
              f"tc.{C.TERM_TYPE}, " \
              f"tc.{C.COUNTERPARTY}, " \
              f"bar.{C.MAIN_ORG} as {C.NAME}, " \
              f"tc.{C.DIRECTION}, " \
              f"tc.{C.REPO_RATE} as {C.RATE}, " \
              f"tc.{C.CONVERTED_BOND_AMT}, " \
              f"tc.{C.BOND_AMT}, " \
              f"tc.{C.REPO_AMT} as {C.TRADE_AMT}, " \
              f"tc.{C.INTEREST_AMT}, " \
              f"tc.{C.SETTLEMENT_DATE}, " \
              f"tc.{C.MATURITY_DATE}, " \
              f"tc.{C.HOLDING_DAYS}, " \
              f"tc.{C.CHECK_STATUS}, " \
              f"tc.{C.TRADE_NO} " \
              f"from {C.COMP_DBNAME}.trade_colrepoes tc " \
              f"left join {C.COMP_DBNAME}.basic_agencies_relation bar " \
              f"on tc.{C.COUNTERPARTY}  = bar.{C.SUB_ORG} " \
              f"where tc.{C.MATURITY_DATE} > '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.SETTLEMENT_DATE} <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.CHECK_STATUS} = 1" \
              f" and tc.{C.DIRECTION} = " + self.direction + \
              f" order by tc.{C.SETTLEMENT_DATE};"

        self.raw = self._get_raw_data(sql)

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        Retrieve raw data from the database.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            pd.DataFrame: The raw data retrieved from the database.
        """

        raw = super()._get_raw_data(sql)

        if raw.empty:
            return pd.DataFrame({})

        # 如果主机构为空，则用子机构的名称代替
        mask = raw[C.NAME].isnull()
        raw.loc[mask, C.NAME] = raw.loc[mask, C.COUNTERPARTY]

        return raw


class IBO(FundTx):

    def __init__(self, start_time: datetime.date, end_time: datetime.date, direction: str) -> None:
        """
        This class represents an IBO transaction.

        Attributes:
            start_time (datetime.date): The start time of the transaction.
            end_time (datetime.date): The end time of the transaction.
            direction (str): The direction of the transaction.
        """

        super().__init__(start_time, end_time, direction)
        self.inst_base = 360
        self.direction = '1' if self.direction == '同业拆入' else '4'

        sql = f"select " \
              f"ti.{C.COUNTERPARTY}, " \
              f"ba.{C.SHORT_NAME}, " \
              f"ba.{C.CODE}, " \
              f"ba.{C.NAME}, " \
              f"ti.{C.TRADER}, " \
              f"ti.{C.TERM_TYPE}, " \
              f"ti.{C.DIRECTION}," \
              f"ti.{C.IBO_RATE} as {C.RATE}," \
              f"ti.{C.IBO_AMT} as {C.TRADE_AMT}," \
              f"ti.{C.HOLDING_DAYS}," \
              f"ti.{C.INTEREST_AMT}," \
              f"ti.{C.SETTLEMENT_DATE}," \
              f"ti.{C.MATURITY_DATE}," \
              f"ti.{C.CHECK_STATUS}," \
              f"ti.{C.TRADE_NO} " \
              f"from {C.COMP_DBNAME}.trade_iboinfos ti " \
              f"left join {C.COMP_DBNAME}.basic_agencies ba " \
              f"on ti.{C.COUNTERPARTY} = ba.{C.NAME} " \
              f"where ti.{C.MATURITY_DATE} > '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and ti.{C.SETTLEMENT_DATE} <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' and ti.{C.CHECK_STATUS} = 1 " \
              f" and ti.{C.DIRECTION} = " + self.direction + \
              f" order by ti.{C.SETTLEMENT_DATE};"

        self.raw = self._get_raw_data(sql)

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        Retrieve raw data from the database.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            pd.DataFrame: The raw data retrieved from the database.
        """

        raw1 = super()._get_raw_data(sql)

        if raw1.empty:
            return raw1

        # 补全拆借业务明细raw1中缺失的code, shortname, name
        sql = f"select distinct " \
              f"ti.{C.COUNTERPARTY}, " \
              f"ba.{C.CODE}, " \
              f"ba.{C.SHORT_NAME}, " \
              f"ba.{C.NAME} " \
              f"from {C.COMP_DBNAME}.trade_iboinfos ti " \
              f"left join {C.COMP_DBNAME}.basic_agencies ba " \
              f"on ti.{C.COUNTERPARTY} = ba.{C.SHORT_NAME} " \
              f"where ba.{C.NAME} != '';"

        raw2 = get_raw(create_conn(), sql)
        df_merged = raw1.merge(raw2, on=C.COUNTERPARTY, how='left', suffixes=('_raw1', '_raw2'))

        raw1[C.SHORT_NAME] = df_merged[C.SHORT_NAME + '_raw2'].combine_first(df_merged[C.SHORT_NAME + '_raw1'])
        raw1[C.CODE] = df_merged[C.CODE + '_raw2'].combine_first(df_merged[C.CODE + '_raw1'])
        raw1[C.NAME] = df_merged[C.NAME + '_raw2'].combine_first(df_merged[C.NAME + '_raw1'])

        return raw1


if __name__ == '__main__':
    s_t = datetime.date(2017, 1, 1)
    e_t = datetime.date(2017, 12, 31)
    # repo = Repo(s_t, e_t, '正回购')
    # print(repo.daily_data(s_t, e_t, '正回购'))
    ibo = IBO(s_t, e_t, '同业拆入')
    print(ibo.daily_data(s_t, e_t, '同业拆入'))
