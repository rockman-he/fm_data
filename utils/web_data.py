# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: This module contains the FundDataHandler class
# which provides methods for displaying transaction data on a web page.
import datetime

from typing import Dict, List

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy

from bond_tx import SecurityTx
from fund_tx import FundTx
from utils.db_util import Constants as C
from utils.market_util import MarketUtil


# 将数据处理后显示到web页面上
class FundDataHandler:
    """
    A utility class for displaying transaction data on a web page.

    Attributes:
        tx (FundTx): The transaction to display.
    """

    def __init__(self, txn: FundTx) -> None:
        """
        Initialize a FundDataHandler instance.

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


class SecurityDataHandler:
    """
    A class used to handle security data.

    Attributes
    ----------
    tx : SecurityTx
        The transaction to handle.
    raw : pd.DataFrame
        The raw data of all bonds.
    inst_rate_bond : set
        The set of bond types that are considered as interest rate bonds.
    """

    def __init__(self, txn: SecurityTx) -> None:
        """
        Constructs all the necessary attributes for the SecurityDataHandler object.

        Parameters
        ----------
            txn : SecurityTx
                The transaction to handle.
        """
        self.tx = txn
        self.raw = self._profits_data_all()
        self.yield_all = self.period_yield_all()

        # 利率债的sectype
        self.inst_rate_bond = {0, 1, 6, 11}

    def get_raw(self) -> pd.DataFrame:
        """
        Returns the raw data of all bonds.

        Returns
        -------
        pd.DataFrame
            The raw data of all bonds.
        """

        return self.raw

    def _profits_data_all(self) -> pd.DataFrame:

        """
        Returns the profits data of all bonds.

        Returns
        -------
        pd.DataFrame
            The data of all bonds.
        """

        bonds = self.tx.get_holded_bonds_info()

        if bonds.empty:
            return pd.DataFrame({})
        bond_codes = bonds[C.BOND_CODE].tolist()
        bond_all = pd.DataFrame({})

        for bond_code in bond_codes:
            bond_all = pd.concat([bond_all, self.tx.sum_all_profits(bond_code)], ignore_index=True)

        bond_all = pd.merge(bond_all, bonds[[C.BOND_CODE, C.ISSUE_ORG]], on=C.BOND_CODE, how='left')

        return bond_all

    def daily_yield_all(self) -> pd.DataFrame:

        """
        Returns the daily yield of all bonds.

        Returns
        -------
        pd.DataFrame
            The daily yield of all bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self._cal_daily_yield(self.raw)

        return raw_group

    def daily_yield_inst_rate_bond(self) -> pd.DataFrame:

        """
        Returns the daily yield of interest rate bonds.

        Returns
        -------
        pd.DataFrame
            The daily yield of interest rate bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self._cal_daily_yield(self.raw[self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def daily_yield_credit_bond(self) -> pd.DataFrame:

        """
        Returns the daily yield of credit bonds.

        Returns
        -------
        pd.DataFrame
            The daily yield of credit bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self._cal_daily_yield(self.raw[~self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def yield_all_cum_by(self, start_time: datetime.date, end_time: datetime.date, by_type: str) -> List[pd.DataFrame]:

        """
        Returns the cumulative daily yield of all bonds.

        Parameters
        ----------
        start_time : datetime.date
            The start time of the cumulative period.
        end_time : datetime.date
            The end time of the cumulative period.

        Returns
        -------
        List[pd.DataFrame]
            The cumulative daily yield of all bonds.
        """

        bonds = self.tx.get_holded_bonds_info()
        bond_list = []

        # print(bonds[by_type].tolist())

        for one_type in set(bonds[by_type].tolist()):
            bond = self.raw[self.raw[by_type] == one_type]
            # print('-------------------')
            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            #     print(bond)

            fixed_columns = [C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT]
            dynamic_columns = [col for col in bond.columns if col not in fixed_columns + [C.DATE]]

            # 构建agg函数字典
            agg_dict = {col: 'sum' for col in fixed_columns}  # 固定列使用 sum 汇总
            agg_dict.update({col: 'first' for col in dynamic_columns})  # 动态列取 first

            # groupby并聚合
            bond = bond.groupby(C.DATE).agg(agg_dict)

            bond_list.append(self._cal_daily_yield_cum(bond, start_time, end_time))

        return bond_list

    def yield_all_cum_by_code(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        # bonds = self.tx.get_holded_bonds_info()
        # bond_list = []
        #
        # for bond_code in bonds[C.BOND_CODE].tolist():
        #     bond = self.raw[self.raw[C.BOND_CODE] == bond_code]
        #     bond_list.append(self._cal_daily_yield_cum(bond, start_time, end_time))

        bond_list = self.yield_all_cum_by(start_time, end_time, C.BOND_CODE)

        return self.bond_yield_format(bond_list, start_time, end_time, [C.BOND_CODE, C.BOND_NAME])

    def yield_all_cum_by_market(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        bond_list = self.yield_all_cum_by(start_time, end_time, C.MARKET_CODE)

        return self.bond_yield_format(bond_list, start_time, end_time, [C.MARKET_CODE])

    def yield_all_cum_by_org(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        bond_list = self.yield_all_cum_by(start_time, end_time, C.ISSUE_ORG)

        return self.bond_yield_format(bond_list, start_time, end_time, [C.ISSUE_ORG])

    def bond_yield_all_cum_test(self, start_time: datetime.date, end_time: datetime.date):

        bonds = self.tx.get_holded_bonds_info()
        bond_list = []

        for bond_code in bonds[C.BOND_CODE].tolist():
            bond = self.raw[self.raw[C.BOND_CODE] == bond_code]
            # bond[C.BOND_TYPE] = ''
            # bond_list.append(self._cal_daily_yield_cum(bond, start_time, end_time))
            bond_list.append(bond)

        return bond_list

    def daily_yield_all_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        Returns the cumulative daily yield of all bonds.

        Parameters
        ----------
        start_time : datetime.date
            The start time of the cumulative period.
        end_time : datetime.date
            The end time of the cumulative period.

        Returns
        -------
        pd.DataFrame
            The cumulative daily yield of all bonds.
        """

        return self._cal_daily_yield_cum(self.daily_yield_all(), start_time, end_time)

    def daily_yield_inst_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        Returns the cumulative daily yield of interest rate bonds.

        Parameters
        ----------
        start_time : datetime.date
            The start time of the cumulative period.
        end_time : datetime.date
            The end time of the cumulative period.

        Returns
        -------
        pd.DataFrame
            The cumulative daily yield of interest rate bonds.
        """

        return self._cal_daily_yield_cum(self.daily_yield_inst_rate_bond(), start_time, end_time)

    def daily_yield_credit_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        Returns the cumulative daily yield of credit bonds.

        Parameters
        ----------
        start_time : datetime.date
            The start time of the cumulative period.
        end_time : datetime.date
            The end time of the cumulative period.

        Returns
        -------
        pd.DataFrame
            The cumulative daily yield of credit bonds.7
        """

        return self._cal_daily_yield_cum(self.daily_yield_credit_bond(), start_time, end_time)
        # print(self.raw[~self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])
        # return self._cal_daily_yield_cum(self.raw[~self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)], start_time,
        #                                  end_time)

    # todo 1.1 保留每日收益率计算，留以后结合负债做收益计算
    def _cal_daily_yield(self, bonds: pd.DataFrame) -> pd.DataFrame:

        """
        Calculates the daily yield of the given bonds.

        Parameters
        ----------
        bonds : pd.DataFrame
            The bonds to calculate the daily yield for.

        Returns
        -------
        pd.DataFrame
            The daily yield of the given bonds.
        """

        # 按天数聚合
        raw_group = bonds.groupby(C.DATE).agg({
            C.HOLD_AMT: lambda x: x.sum(),
            C.CAPITAL_OCCUPY: lambda x: x.sum(),
            C.CAPITAL_GAINS: lambda x: x.sum(),
            C.INST_A_DAY: lambda x: x.sum(),
            C.NET_PROFIT: lambda x: x.sum(),
            C.TOTAL_PROFIT: lambda x: x.sum()
        })
        # todo 1.1.1 每日收益率计算
        raw_group[C.YIELD] = (((raw_group[C.INST_A_DAY] * 365) + raw_group[C.CAPITAL_GAINS] + raw_group[C.NET_PROFIT])
                              / raw_group[C.CAPITAL_OCCUPY] * 100)
        raw_group[C.YIELD_NO_NET_PROFIT] = (((raw_group[C.INST_A_DAY] * 365) + raw_group[C.CAPITAL_GAINS]) /
                                            raw_group[C.CAPITAL_OCCUPY] * 100)

        return raw_group

    def _cal_daily_yield_cum(self, bonds_data: pd.DataFrame, start_time: datetime.date,
                             end_time: datetime.date) -> pd.DataFrame:

        if bonds_data.empty:
            return pd.DataFrame({})

        date_range = pd.date_range(start=start_time, end=end_time)
        df_null = pd.DataFrame(date_range, columns=[C.DATE])

        daily_data = bonds_data.copy()
        daily_data_cum = pd.merge(df_null, daily_data, on=C.DATE, how='left')

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        # daily_data_cum = daily_data_cum.fillna(0)

        first_valid_index = daily_data_cum[C.HOLD_AMT].first_valid_index()

        if first_valid_index != daily_data_cum.index[0]:
            first_valid_row = daily_data_cum.loc[first_valid_index]
            last_invaid_index = first_valid_index - 1

            # 对于其他列，将它们的值设置为首个非空行的值
            for column in daily_data_cum.columns:
                if column not in [C.HOLD_AMT, C.INST_A_DAY, C.CAPITAL_GAINS, C.NET_PROFIT, C.CAPITAL_OCCUPY,
                                  C.TOTAL_PROFIT, C.COST_NET_PRICE]:
                    daily_data_cum.loc[:last_invaid_index, column] = first_valid_row[column]

            # 将第一行至首个非空值的某些行（不包含）间的行赋值为0
            daily_data_cum.loc[:last_invaid_index,
            [C.HOLD_AMT, C.CAPITAL_OCCUPY, C.COST_NET_PRICE, C.COST_FULL_PRICE, C.TOTAL_PROFIT]] = 0

        # 计算累计利息收入
        daily_data_cum[C.INST_A_DAY] = daily_data_cum[C.INST_A_DAY].infer_objects(copy=False).fillna(0.0)
        # daily_data_cum[C.INST_A_DAY].fillna(0.0, inplace=True)
        daily_data_cum[C.INST_DAYS] = daily_data_cum[C.INST_A_DAY].cumsum()

        # 计算累计资本利得
        daily_data_cum[C.CAPITAL_GAINS] = daily_data_cum[C.CAPITAL_GAINS].fillna(0.0)
        daily_data_cum[C.CAPITAL_GAINS_CUM] = daily_data_cum[C.CAPITAL_GAINS].cumsum()

        # 计算累计净价浮盈
        daily_data_cum[C.NET_PROFIT] = daily_data_cum[C.NET_PROFIT].fillna(0.0)
        # daily_data_cum[C.NET_PROFIT_SUB] = daily_data_cum[C.NET_PROFIT] - daily_data_cum[C.NET_PROFIT].iloc[0]
        # daily_data_cum[C.NET_PROFIT_SUB] = (daily_data_cum[C.NET_PROFIT] -
        #                                     daily_data_cum.loc[first_valid_index, C.NET_PROFIT])

        if len(daily_data_cum) == 1:
            daily_data_cum[C.NET_PROFIT_SUB] = daily_data_cum[C.NET_PROFIT]
        else:
            daily_data_cum[C.NET_PROFIT_SUB] = (daily_data_cum[C.NET_PROFIT] -
                                                daily_data_cum.loc[first_valid_index, C.NET_PROFIT])

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        # 如果当日无持仓，忽略当日的净价浮盈
        daily_data_cum[C.HOLD_AMT] = daily_data_cum[C.HOLD_AMT].fillna(0.0)
        daily_data_cum.loc[daily_data_cum[C.HOLD_AMT] == 0, C.NET_PROFIT_SUB] = 0.0

        # 计算累计总收益
        daily_data_cum[C.TOTAL_PROFIT_CUM] = daily_data_cum[C.NET_PROFIT_SUB] + daily_data_cum[C.CAPITAL_GAINS_CUM] + \
                                             daily_data_cum[C.INST_DAYS]

        # 计算daily_data_cum[C.CAPITAL_OCCUPY]的累积和
        # daily_all_cum[C.CAPITAL_OCCUPY] = daily_all_cum[C.CAPITAL_OCCUPY].fillna(0)
        daily_data_cum[C.CAPITAL_OCCUPY_CUM] = daily_data_cum[C.CAPITAL_OCCUPY].cumsum()

        # 将C.CAPITAL_OCCUPY列中的非零值设置为1
        daily_data_cum['non_zero'] = (daily_data_cum[C.CAPITAL_OCCUPY] != 0).astype(int)
        # 对于资金占用为0的情形，统计实际资金占用统计天数
        daily_data_cum[C.WORK_DAYS] = daily_data_cum['non_zero'].cumsum()
        # 删除临时列
        del daily_data_cum['non_zero']

        # 计算区间收益的值
        daily_data_cum[C.YIELD_CUM] = ((daily_data_cum[C.INST_DAYS] * 365 /
                                        daily_data_cum[C.WORK_DAYS] + daily_data_cum[C.CAPITAL_GAINS_CUM] +
                                        daily_data_cum[C.NET_PROFIT_SUB]) /
                                       (daily_data_cum[C.CAPITAL_OCCUPY_CUM] /
                                        daily_data_cum[C.WORK_DAYS]) * 100)

        daily_data_cum = daily_data_cum.infer_objects(copy=False).ffill()

        # print('xxxx')
        #
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        return daily_data_cum

    def period_yield_all(self) -> pd.DataFrame:
        """
        Returns the period yield of all bonds.

        Returns
        -------
        pd.DataFrame
            The period yield of all bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        bond_group = self.raw.groupby(C.BOND_CODE).agg({
            C.BOND_NAME: lambda x: x.iloc[0],
            C.MARKET_CODE: lambda x: x.iloc[0],
            C.HOLD_AMT: lambda x: x.mean(),
            C.CAPITAL_OCCUPY: lambda x: x.mean(),
            C.CAPITAL_GAINS: lambda x: x.sum(),
            C.INST_A_DAY: lambda x: x.sum()
        })
        bond_group.rename(columns={C.INST_A_DAY: C.INST_DAYS}, inplace=True)
        bond_group[C.COST_NET_PRICE] = bond_group[C.CAPITAL_OCCUPY] / bond_group[C.HOLD_AMT] * 100

        # 对每支债券做收益计算
        for row in bond_group.index:
            bond_code = row
            bond = self.raw[self.raw[C.BOND_CODE] == bond_code]

            # 如果卖空，净价浮盈为0
            if bond.iloc[-1][C.HOLD_AMT] == 0:
                bond_group.loc[row, C.NET_PROFIT] = 0
            # 如果统计天数为1天，净价浮盈为当日净价浮盈
            elif len(bond) == 1:
                bond_group.loc[row, C.NET_PROFIT] = bond.iloc[0][C.NET_PROFIT]
            # 否则，净价浮盈为区间最后一天净价浮盈减去区间第一天净价浮盈
            else:
                bond_group.loc[row, C.NET_PROFIT] = bond.iloc[-1][C.NET_PROFIT] - bond.iloc[0][C.NET_PROFIT]

            bond_group.loc[row, C.TOTAL_PROFIT] = (bond_group.loc[row, C.CAPITAL_GAINS] +
                                                   bond_group.loc[row, C.NET_PROFIT] +
                                                   bond_group.loc[row, C.INST_DAYS])

            # 无持仓则没有资金占用，区间内不计入持仓天数
            count_days = len(bond.loc[bond[C.HOLD_AMT] != 0])
            # todo 1.2 年化收益率计算方式
            bond_group.loc[row, C.YIELD] = (bond_group.loc[row, C.TOTAL_PROFIT] * 365 /
                                            bond_group.loc[row, C.CAPITAL_OCCUPY] / count_days * 100)
            bond_group.loc[row, C.YIELD_NO_NET_PROFIT] = ((bond_group.loc[row, C.TOTAL_PROFIT] -
                                                           bond_group.loc[row, C.NET_PROFIT]) * 365 /
                                                          bond_group.loc[row, C.CAPITAL_OCCUPY] / count_days * 100)

        return bond_group

    def period_yield_bond(self, bond_code: str) -> pd.DataFrame:
        """
        Returns the period yield of the bond with the given code.

        Parameters
        ----------
        bond_code : str
            The code of the bond to return the period yield for.

        Returns
        -------
        pd.DataFrame
            The yield of the bond with the given code.
        """

        if self.yield_all.empty or bond_code not in self.yield_all.index.tolist():
            return pd.DataFrame({})

        return self.yield_all.loc[[bond_code]]

    @staticmethod
    def bond_yield_format_test(raws, start_time: datetime.date, end_time: datetime.date, first_column) -> pd.DataFrame:
        """
        Formats the bond yield data.

        Parameters
        ----------
        raw : pd.DataFrame
            The raw data to format.

        Returns
        -------
        pd.DataFrame
            The formatted data.
            :param first_column:
            :param start_time:
            :param end_time:
        """

        # 创建一个空的DataFrame
        df = pd.DataFrame(columns=[first_column, C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
                                   C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM])

        i = 0
        workdays = (end_time - start_time).days + 1

        for raw in raws:
            # workdays = raw.iloc[-1][C.WORK_DAYS]
            insts = raw.iloc[-1][C.INST_DAYS]
            capital_gains = raw[C.CAPITAL_GAINS].sum()
            net_profit = raw.iloc[-1][C.NET_PROFIT_SUB]

            df.loc[i] = [raw.iloc[0][first_column],
                         '{:,.2f}'.format(raw[C.HOLD_AMT].sum() / workdays),
                         '{:,.2f}'.format(raw.iloc[-1][C.CAPITAL_OCCUPY_CUM] / workdays),
                         '{:,.2f}'.format(insts),
                         '{:,.2f}'.format(net_profit),
                         '{:,.2f}'.format(capital_gains),
                         '{:,.2f}'.format(insts + capital_gains + net_profit),
                         '{:.4f}'.format(raw.iloc[-1][C.YIELD_CUM])]
            i = i + 1

        return df

    @staticmethod
    def bond_yield_format(raws, start_time: datetime.date, end_time: datetime.date, columns: List[str]) -> pd.DataFrame:
        """

        :param raws:
        :param start_time:
        :param end_time:
        :param columns:
        :return:
        """

        # 创建一个空的DataFrame
        df = pd.DataFrame(columns=(columns + [C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
                                              C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]))

        i = 0
        workdays = (end_time - start_time).days + 1

        for raw in raws:
            # workdays = raw.iloc[-1][C.WORK_DAYS]
            insts = raw.iloc[-1][C.INST_DAYS]
            capital_gains = raw[C.CAPITAL_GAINS].sum()
            net_profit = raw.iloc[-1][C.NET_PROFIT_SUB]

            temp = []

            for column in columns:
                temp += [raw.iloc[0][column]]

            df.loc[i] = temp + ['{:,.2f}'.format(raw[C.HOLD_AMT].sum() / workdays),
                                '{:,.2f}'.format(raw.iloc[-1][C.CAPITAL_OCCUPY_CUM] / workdays),
                                '{:,.2f}'.format(insts),
                                '{:,.2f}'.format(net_profit),
                                '{:,.2f}'.format(capital_gains),
                                '{:,.2f}'.format(insts + capital_gains + net_profit),
                                '{:.4f}'.format(raw.iloc[-1][C.YIELD_CUM])]
            i = i + 1

        return df


if __name__ == "__main__":
    list = ['a', 'b', 'c']
    print(list + ['d'])
