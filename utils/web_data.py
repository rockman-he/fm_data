# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: This module contains the FundDataHandler class
# which provides methods for displaying transaction data on a web page.
import datetime

from typing import Dict, List

import pandas as pd

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
            txn : 该时间区间内的交易数据
        """
        self.tx = txn
        self.raw = self.tx.get_all_profit_data()
        # self.yield_all = self.period_yield_all()

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

    def get_holding_bonds_endtime(self) -> pd.DataFrame:
        """
        返回在统计区间末时点的持有债券数据，额外包含了债券基础信息
        :return: 在统计区间末时点的持有债券数据
        """

        holded = self.tx.get_holding_bonds_endtime()
        bond_info = self.tx.get_holded_bonds_info()

        if bond_info.empty:
            return pd.DataFrame({})

        holded = pd.merge(holded, bond_info[[C.BOND_CODE, C.BOND_TYPE, C.COUPON_RATE_ISSUE, C.COUPON_RATE_CURRENT,
                                             C.ISSUE_AMT, C.ISSUE_PRICE, C.ISSUE_ORG, C.MATURITY]],
                          on=C.BOND_CODE,
                          how='left')

        return holded

    def get_inst_bonds(self, bonds: pd.DataFrame) -> pd.DataFrame:
        """
        返回bonds中的利率债

        Returns
        -------
        pd.DataFrame
            bonds中的利率债
        """

        return bonds[bonds[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)]

    def get_credit_bonds(self, bonds: pd.DataFrame) -> pd.DataFrame:
        """
        返回bonds中的信用债

        Returns
        -------
        pd.DataFrame
            bonds中的信用债
        """

        return bonds[~bonds[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)]

    def daily_yield_all(self) -> pd.DataFrame:

        """
        单日收益情况（全部债券）

        Returns
        -------
        pd.DataFrame
            The daily yield of all bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw)

        return raw_group

    def daily_yield_inst_rate_bond(self) -> pd.DataFrame:

        """
        单日收益情况（利率债券）

        Returns
        -------
        pd.DataFrame
            The daily yield of interest rate bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw[self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def daily_yield_credit_bond(self) -> pd.DataFrame:

        """
        单日收益情况（信用债）

        Returns
        -------
        pd.DataFrame
            The daily yield of credit bonds.
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw[~self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def _yield_cum_by(self, start_time: datetime.date, end_time: datetime.date, by_type: str) -> List[pd.DataFrame]:
        """
        按by_type（如C.BOND_CODE)取全量数据的分类子集，然后计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param by_type: 分组类型
        :return: 每个分组后的收益情况
        """

        # 持有债券的基础信息
        bonds_info = self.tx.get_holded_bonds_info()
        bond_list = []

        # 对每一种分组类型进行计算
        for one_type in set(bonds_info[by_type].tolist()):
            bond = self.raw[self.raw[by_type] == one_type]
            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            #     print(bond)

            # 对于需要计算的固定列，使用 sum 汇总
            fixed_columns = [C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT]
            # 对于动态列，取第一行的值
            dynamic_columns = [col for col in bond.columns if col not in fixed_columns + [C.DATE]]

            # 构建agg函数字典
            agg_dict = {col: 'sum' for col in fixed_columns}  # 固定列使用 sum 汇总
            agg_dict.update({col: 'first' for col in dynamic_columns})  # 动态列取 first

            # 由于_cal_daily_yield_cum要求日期项不能重复，先用groupby按日期聚合
            bond = bond.groupby(C.DATE).agg(agg_dict)
            # 分组数据计算后形成列表
            bond_list.append(self.cal_period_yield_cum(bond, start_time, end_time))

        return bond_list

    def yield_cum_by_code(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按债券代码分组
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 按债券代码分组后的收益情况
        """

        bond_list = self._yield_cum_by(start_time, end_time, C.BOND_CODE)

        return self.yield_data_format(bond_list, start_time, end_time, [C.BOND_CODE, C.BOND_NAME])

    def yield_cum_by_market(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:
        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按市场代码分组
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 按市场代码分组后的收益情况
        """

        bond_list = self._yield_cum_by(start_time, end_time, C.MARKET_CODE)

        return self.yield_data_format(bond_list, start_time, end_time, [C.MARKET_CODE])

    def yield_cum_by_org(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:
        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按发行机构分组
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 按发行机构分组后的收益情况
        """
        bond_list = self._yield_cum_by(start_time, end_time, C.ISSUE_ORG)

        return self.yield_data_format(bond_list, start_time, end_time, [C.ISSUE_ORG])

    def period_yield_all_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按天数聚合（全部债券）

        Parameters
        ----------
        start_time : datetime.date
            开始时间
        end_time : datetime.date
            结束时间

        Returns
        -------
        pd.DataFrame
            按天数聚合后的区间收益情况
        """

        return self.cal_period_yield_cum(self.daily_yield_all(), start_time, end_time)

    def period_yield_inst_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按天数聚合（利率债券）

        Parameters
        ----------
        start_time : datetime.date
            开始时间
        end_time : datetime.date
            结束时间

        Returns
        -------
        pd.DataFrame
            按天数聚合后的区间收益情况
        """

        return self.cal_period_yield_cum(self.daily_yield_inst_rate_bond(), start_time, end_time)

    def period_yield_credit_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，按天数聚合（信用债）

        Parameters
        ----------
        start_time : datetime.date
            开始时间
        end_time : datetime.date
            结束时间

        Returns
        -------
        pd.DataFrame
            按天数聚合后的区间收益情况
        """

        return self.cal_period_yield_cum(self.daily_yield_credit_bond(), start_time, end_time)

    # 1.1 保留单日收益率计算，留以后结合负债做收益计算
    @staticmethod
    def cal_daily_yield(bond_data: pd.DataFrame) -> pd.DataFrame:

        """
        按每天C.DATE进行聚合，计算单日资金占用，资本利得，净价浮盈，利息收入等收益相关数据

        Parameters
        ----------
        bond_data : pd.DataFrame
            The data to calculate the daily yield for.

        Returns
        -------
        pd.DataFrame
            The daily yield of the given data.
        """

        # 按天数聚合
        raw_group = bond_data.groupby(C.DATE).agg({
            C.HOLD_AMT: lambda x: x.sum(),
            C.CAPITAL_OCCUPY: lambda x: x.sum(),
            C.CAPITAL_GAINS: lambda x: x.sum(),
            C.INST_A_DAY: lambda x: x.sum(),
            C.NET_PROFIT: lambda x: x.sum(),
            C.TOTAL_PROFIT: lambda x: x.sum()
        })
        # 1.1.1 每日收益率计算
        raw_group[C.YIELD] = (((raw_group[C.INST_A_DAY] * 365) + raw_group[C.CAPITAL_GAINS] + raw_group[C.NET_PROFIT])
                              / raw_group[C.CAPITAL_OCCUPY] * 100)
        raw_group[C.YIELD_NO_NET_PROFIT] = (((raw_group[C.INST_A_DAY] * 365) + raw_group[C.CAPITAL_GAINS]) /
                                            raw_group[C.CAPITAL_OCCUPY] * 100)

        return raw_group

    @staticmethod
    def cal_period_yield_cum(bonds_data: pd.DataFrame, start_time: datetime.date,
                             end_time: datetime.date) -> pd.DataFrame:
        """
        计算每日资金占用，资本利得，净价浮盈，利息收入，总收益和每日收益率等收益情况的累计值。注意：单日数据不能有重复值（不能存在多个相同日期）
        :param bonds_data: 要计算的债券数据
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 每日收益情况（累加）
        """

        if bonds_data.empty:
            return pd.DataFrame({})

        # 生成一个时间序列
        date_range = pd.date_range(start=start_time, end=end_time)
        df_null = pd.DataFrame(date_range, columns=[C.DATE])

        daily_data = bonds_data.copy()
        daily_data_cum = pd.merge(df_null, daily_data, on=C.DATE, how='left')

        # 在统计时间区间内，存在一开始就没有数据的情况，需要对这些日期进行填充
        first_valid_index = daily_data_cum[C.HOLD_AMT].first_valid_index()

        # 如果第一个非空行不是第一行，将第一行至首个非空值的某些行（不包含）间的行赋值为首个非空行的值
        if first_valid_index != daily_data_cum.index[0]:
            first_valid_row = daily_data_cum.loc[first_valid_index]
            last_invaid_index = first_valid_index - 1

            # 除固定列外，对于其他列，将它们的值设置为首个非空行的值
            for column in daily_data_cum.columns:
                if column not in [C.HOLD_AMT, C.INST_A_DAY, C.CAPITAL_GAINS, C.NET_PROFIT, C.CAPITAL_OCCUPY,
                                  C.TOTAL_PROFIT, C.COST_NET_PRICE]:
                    daily_data_cum.loc[:last_invaid_index, column] = first_valid_row[column]

            # 将第一行至首个非空值的某些行（不包含）间的行赋值为0
            daily_data_cum.loc[:last_invaid_index, [C.HOLD_AMT, C.CAPITAL_OCCUPY, C.COST_NET_PRICE,
                                                    C.COST_FULL_PRICE, C.TOTAL_PROFIT]] = 0

        # 计算累计利息收入
        daily_data_cum[C.INST_A_DAY] = daily_data_cum[C.INST_A_DAY].infer_objects(copy=False).fillna(0.0)
        daily_data_cum[C.INST_DAYS] = daily_data_cum[C.INST_A_DAY].cumsum()

        # 计算累计资本利得
        daily_data_cum[C.CAPITAL_GAINS] = daily_data_cum[C.CAPITAL_GAINS].fillna(0.0)
        daily_data_cum[C.CAPITAL_GAINS_CUM] = daily_data_cum[C.CAPITAL_GAINS].cumsum()

        # 计算累计净价浮盈
        daily_data_cum[C.NET_PROFIT] = daily_data_cum[C.NET_PROFIT].fillna(0.0)
        # 如果只有一行数据，净价浮盈为当日的净价浮盈
        if len(daily_data_cum) == 1:
            daily_data_cum[C.NET_PROFIT_SUB] = daily_data_cum[C.NET_PROFIT]
        else:
            daily_data_cum[C.NET_PROFIT_SUB] = (daily_data_cum[C.NET_PROFIT] -
                                                daily_data_cum.loc[first_valid_index, C.NET_PROFIT])

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        # 如果当日无持仓，当日的净价浮盈为0
        daily_data_cum[C.HOLD_AMT] = daily_data_cum[C.HOLD_AMT].fillna(0.0)
        daily_data_cum.loc[daily_data_cum[C.HOLD_AMT] == 0, C.NET_PROFIT_SUB] = 0.0

        # 计算累计总收益
        daily_data_cum[C.TOTAL_PROFIT_CUM] = (daily_data_cum[C.NET_PROFIT_SUB] + daily_data_cum[C.CAPITAL_GAINS_CUM] +
                                              daily_data_cum[C.INST_DAYS])

        # 计算daily_data_cum[C.CAPITAL_OCCUPY]的累积和
        daily_data_cum[C.CAPITAL_OCCUPY] = daily_data_cum[C.CAPITAL_OCCUPY].fillna(0)
        daily_data_cum[C.CAPITAL_OCCUPY_CUM] = daily_data_cum[C.CAPITAL_OCCUPY].cumsum()

        # 将C.CAPITAL_OCCUPY列中的非零值设置为1
        daily_data_cum['non_zero'] = (daily_data_cum[C.CAPITAL_OCCUPY] != 0).astype(int)
        # 对于资金占用为0的情形，统计实际资金占用统计天数
        daily_data_cum[C.WORK_DAYS] = daily_data_cum['non_zero'].cumsum()
        # 删除临时列
        del daily_data_cum['non_zero']

        # 计算区间收益的值，基数按365天计算
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

    @staticmethod
    def yield_data_format(raw_data: List[pd.DataFrame], start_time: datetime.date, end_time: datetime.date,
                          columns: List[str]) -> pd.DataFrame:
        """
        将收益数据格式化，更好的展示到web页面的dataframe上
        :param raw_data: 收益数据的集合，每个元素为一个DataFrame，每个DataFrame为一个分组的收益数据
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param columns: 需要展示的列，该列多为文本型数据无需做数值计算，所以在计算中取raw_data的第一行数据
        :return: 格式化后的收益数据
        """

        # 创建一个空的DataFrame， columns包含了要展示的列
        df = pd.DataFrame(columns=(columns + [C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
                                              C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]))

        i = 0
        count_days = (end_time - start_time).days + 1

        for raw in raw_data:

            insts = raw.iloc[-1][C.INST_DAYS]
            capital_gains = raw[C.CAPITAL_GAINS].sum()
            net_profit = raw.iloc[-1][C.NET_PROFIT_SUB]

            temp = []

            for column in columns:
                temp += [raw.iloc[0][column]]

            # 格式化
            df.loc[i] = temp + ['{:,.2f}'.format(raw[C.HOLD_AMT].sum() / count_days),
                                '{:,.2f}'.format(raw.iloc[-1][C.CAPITAL_OCCUPY_CUM] / count_days),
                                '{:,.2f}'.format(insts),
                                '{:,.2f}'.format(net_profit),
                                '{:,.2f}'.format(capital_gains),
                                '{:,.2f}'.format(insts + capital_gains + net_profit),
                                '{:.4f}'.format(raw.iloc[-1][C.YIELD_CUM])]
            i = i + 1

        return df
