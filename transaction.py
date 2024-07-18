# Author: RockMan
# CreateTime: 2024/7/15
# FileName: transaction
# Description: simple introduction of the code
import datetime
from abc import ABC, abstractmethod

import pandas as pd
import streamlit as st

from utils.database_util import Constants as C, DBUtil


class Transaction(ABC):
    """
    This is an abstract base class for all repurchase and lending transactions.
    """

    def __init__(self):
        """
        Initialize a Transaction instance.

        """
        self.start_time = None
        self.end_time = None
        self.direction = None
        self.raw_data = pd.DataFrame({})

    @abstractmethod
    def _get_raw_data(self, start_time: datetime.date, end_time: datetime.date,
                      direction: str) -> pd.DataFrame:
        """
        Abstract method to retrieve raw transaction data from a database.

        This method must be implemented in any class that inherits from the Transaction abstract base class.

        Args:
            start_time (datetime): The start time of the raw transaction data to be retrieved.
            end_time (datetime): The end time of the raw transaction data to be retrieved.
            direction (str): The direction of the transaction (e.g., '正回购' or '逆回购').

        Returns:
            pd.DataFrame: A pandas DataFrame containing the raw transaction data.

        Note:
            This is an abstract method and must be overridden in subclasses.
        """

        raise NotImplementedError


class Repo(Transaction):

    @st.cache_data
    def _get_raw_data(_self, start_time: datetime.date, end_time: datetime.date,
                      direction: str) -> pd.DataFrame:
        """
        Method to retrieve raw transaction data from a database.

        Args:
            start_time (datetime.date): The start time of the raw transaction data to be retrieved.
            end_time (datetime.date): The end time of the raw transaction data to be retrieved.
            direction (str): The direction of the transaction (e.g., '正回购' or '逆回购').

        Returns:
            pd.DataFrame: A pandas DataFrame containing the raw transaction data.
            包含和

        This method first checks if the start time is later than the end time, in which case it returns
        an empty DataFrame.
        Otherwise, it executes a SQL query to get the raw transaction data from the 'upsrod.trade_colrepoes tc' table.
        The resulting DataFrame is then processed to handle missing values,
        duplicate entries, and to calculate additional metrics.
        """

        # 正回购or逆回购
        # side = '4' if self.direction == '正回购' else '1'

        _self.start_time = start_time
        _self.end_time = end_time
        _self.direction = direction

        _self.side = '4' if _self.direction == '正回购' else '1'
        _sql = f"select tc.{C.TRADE_NO}, tc.{C.TERM_TYPE}, tc.{C.COUNTERPARTY}, bar.{C.MAIN_ORG}, " \
               f"tc.{C.DIRECTION}, tc.{C.REPO_RATE}, tc.{C.CONVERTED_BOND_AMOUNT}, tc.{C.BOND_AMOUNT}, " \
               f"tc.{C.REPO_AMOUNT}, tc.{C.INTEREST_AMOUNT}, tc.{C.SETTLEMENT_DATE}, tc.{C.MATURITY_DATE}, " \
               f"tc.{C.CASH_HOLDING_DAYS}, tc.{C.CHECK_STATUS}, tc.{C.TRADER} " \
               f"from upsrod.trade_colrepoes tc " \
               f"left join upsrod.basic_agencies_relation bar " \
               f"on tc.{C.COUNTERPARTY}  = bar.{C.SUB_ORG} " \
               f"where tc.{C.MATURITY_DATE} > '" + _self.start_time.strftime('%Y-%m-%d') + \
               f"' and tc.{C.SETTLEMENT_DATE} <= '" + \
               _self.end_time.strftime('%Y-%m-%d') + f"' and tc.{C.CHECK_STATUS} = 1 and " + \
               f"tc.{C.DIRECTION} = " + _self.side + \
               f" order by tc.{C.SETTLEMENT_DATE};"

        # 如果用户选择的截至时间晚于起始时间，则返回空df
        if _self.start_time > _self.end_time:
            return pd.DataFrame({})

        # 如果数据已经被加载过，则直接返回
        if _self.raw_data.empty is False:
            return _self.raw_data

        # 从数据库中获取数据
        _self.raw_data = DBUtil().create_conn().query(_sql)

        # 由于upsrod.basic_agencies_relation表中存在一个子机构对应多个主机构的情况，因此按C.TRADE_NO删除重复项，保留第一个出现的数据项
        _self.raw_data.drop_duplicates(C.TRADE_NO, inplace=True)

        # 如果主机构为空，则用子机构的名称代替
        _condition = _self.raw_data[C.MAIN_ORG].isnull()
        _self.raw_data.loc[_condition, C.MAIN_ORG] = _self.raw_data.loc[_condition, C.COUNTERPARTY]

        # C.AS_DT: 实际统计开始时间， C.AE_DT： 实际统计结束时间
        # 增加两列，初始化
        _self.raw_data[C.AS_DT] = _self.raw_data[C.SETTLEMENT_DATE]
        _self.raw_data[C.AE_DT] = _self.raw_data[C.MATURITY_DATE]

        # 对于在统计区间，但是起止时间超出的部分做初始化处理，方便以后计算
        mask = _self.raw_data[C.AS_DT] < pd.to_datetime(_self.start_time)
        _self.raw_data.loc[mask, C.AS_DT] = pd.to_datetime(_self.start_time)

        # 注意：如果C.AE_DT（到期结算日） > end_time，那实际统计日当天也是要计算利息，对于该情况，要加上一天
        mask = _self.raw_data[C.AE_DT] > pd.to_datetime(_self.end_time)
        _self.raw_data.loc[mask, C.AE_DT] = pd.to_datetime(_self.end_time) + datetime.timedelta(days=1)

        # 统计区间的实际计息天数
        _self.raw_data[C.WORK_DAYS] = (_self.raw_data[C.AE_DT] - _self.raw_data[C.AS_DT]).apply(lambda x: x.days)
        # 积数
        _self.raw_data[C.PRODUCT] = _self.raw_data[C.REPO_AMOUNT] * _self.raw_data[C.WORK_DAYS]

        # 统计区间内实际收取的利息，C.INST_DAYS为区间总利息，C.INST_A_DAY为每天的利息
        _self.raw_data[C.INST_DAYS] = (_self.raw_data[C.INTEREST_AMOUNT] / _self.raw_data[C.CASH_HOLDING_DAYS]
                                       * _self.raw_data[C.WORK_DAYS])
        _self.raw_data[C.INST_A_DAY] = _self.raw_data[C.INTEREST_AMOUNT] / _self.raw_data[C.CASH_HOLDING_DAYS]

        return _self.raw_data

    @st.cache_data
    def repo_everyday(_self, start_time: datetime.date, end_time: datetime.date, direction: str) -> pd.DataFrame:

        """
        Method to process the repurchase transaction data on a daily basis.

        Args:
            start_time (datetime.date): The start time of the transaction data to be processed.
            end_time (datetime.date): The end time of the transaction data to be processed.
            direction (str): The direction of the transaction (e.g., '正回购' or '逆回购').

        Returns:
            pd.DataFrame: A pandas DataFrame containing the processed transaction data.
            包含日期、每日回购余额、每日加权利率

        This method first retrieves the raw transaction data using the _get_transaction_data method.
        It then creates a DataFrame for the date range from start_time to end_time,
        and initializes the columns for repurchase amount and interest.
        The method then iterates over the raw data, and for each row,
        it adds the repurchase amount and interest to the corresponding dates in the DataFrame.
        Finally, it calculates the weighted rate for each date and fills any missing values with 0.
        """

        raw_data = _self._get_raw_data(start_time, end_time, direction)

        if raw_data.empty:
            return pd.DataFrame({})

        date_range = pd.date_range(start=start_time, end=end_time, freq='D')
        repo = pd.DataFrame(date_range, columns=[C.AS_DT])
        repo[C.REPO_AMOUNT] = 0.0
        repo[C.INST_DAYS] = 0.0

        # 遍历数据库查询结果
        for row in raw_data.index:
            # 回购金额
            repo_amt = raw_data.loc[row][C.REPO_AMOUNT]
            # 满足统计区间的起始时间
            as_date = raw_data.loc[row][C.AS_DT]
            # 满足统计区间的截至时间
            ae_date = raw_data.loc[row][C.AE_DT]
            # 每天的利息
            inst_a_day = raw_data.loc[row][C.INST_A_DAY]

            # 将起止时间段的回购余额和利息总额进行汇总
            mask = (repo[C.AS_DT] >= as_date) & (repo[C.AS_DT] < ae_date)
            repo.loc[mask, [C.REPO_AMOUNT]] += repo_amt
            repo.loc[mask, [C.INST_DAYS]] += inst_a_day

        repo[C.WEIGHT_RATE] = repo[C.INST_DAYS] * 365 / repo[C.REPO_AMOUNT] * 100
        repo[C.WEIGHT_RATE] = repo[C.WEIGHT_RATE].fillna(0)

        return repo


if __name__ == '__main__':
    s_t = datetime.date(2023, 1, 1)
    e_t = datetime.date(2023, 6, 1)
    repo = Repo()
    c = repo.repo_everyday(s_t, e_t, '正回购')
    print(c)
