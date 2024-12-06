# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: This module contains the FundDataHandler class
# which provides methods for displaying transaction data on a web page.
from datetime import datetime, timedelta

from typing import Dict, List, Union

import pandas as pd
from pandas import DataFrame

from bond_tx import SecurityTx, BondTx, CDTx
from fund_tx import FundTx, Repo, IBO
from utils.db_util import Constants as C
from utils.market_util import MarketUtil
from utils.time_util import TimeUtil
from utils.txn_factory import TxFactory


def format_output_keep_types(df: pd.DataFrame, format_col: Dict = None) -> pd.DataFrame:
    """
    格式化列名并调整显示，但不改变数值列的类型。
    """

    if format_col:
        # 替换列名
        df = df.rename(columns=format_col)

    # 格式化显示：保留原类型
    formatted_df = df.copy()
    for col in formatted_df.select_dtypes(include=['number']).columns:
        formatted_df[col] = formatted_df[col].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else x)

    return formatted_df


# 将数据处理后显示到web页面上
class FundDataHandler:
    """
    处理资金交易数据的工具类。

    Attributes:
        tx (FundTx): 要显示的交易对象.
        d (int): 交易方向，资金融入为4，资金融出为1
    """

    def __init__(self, txn: FundTx) -> None:
        """
        构造函数
        Args:
            txn (FundTx): 资金交易类型.
        """

        self.tx = txn
        self.d = 100

        # self.out_raw = {}

    def set_direction(self, direction: str):
        self.d = 4 if direction == C.REPO or direction == C.IBO else 1

    def check_set_d(self):
        """
        检查方向函数是否被设置. 如何没有，抛出错误警告.
        """
        if self.d == 100:
            raise ValueError("Direction has not been set. Please set the direction before proceeding.")

    def daily_data(self) -> pd.DataFrame:
        """
        将FundTx的每日交易与资金市场利率按日期合并.

        Returns:
            pd.DataFrame: [C.AS_DT, C.TRADE_AMT, C.INST_DAYS, C.WEIGHT_RATE, C.R001, C.R007, C.SHIBOR_ON, C.SHIBOR_1W]
        """

        # daily = self.daily_raw.setdefault(self.d, self.tx.daily_data(self.d))

        self.check_set_d()
        daily = self.tx.daily_data(self.d)

        # daily = self.out_raw.setdefault(['daily', self.d], self.tx.daily_data(self.d))

        if daily.empty:
            return daily

        market_irt = MarketUtil().get_irt(self.tx.start_time, self.tx.end_time)

        return pd.merge(daily, market_irt, left_on=C.AS_DT, right_on=C.DATE, how='left')

    def party_rank(self) -> pd.DataFrame:
        """
        按照主机构的日均余额进行排名，返回统计数据.

        Returns:
            pd.DataFrame: [C.NAME, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE].
        """

        # return self.tx.party_rank()
        self.check_set_d()

        if self.tx.raw_by_direction(self.d).empty:
            return pd.DataFrame({})

        party = self.tx.groupby_column(C.NAME, self.d)
        # party = self.out_raw.setdefault([C.NAME, self.d], self.tx.groupby_column(C.NAME, self.d))

        return party

    def party_rank_n(self, n: int = 10) -> pd.DataFrame:
        """
        按照主机构的日均余额进行排名，返回“前n个 + 其他”，n默认为10.
        Args:
            n: 显示前n个主机构，默认为10.
        Returns:
            pd.DataFrame: [C.NAME, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE].
        """

        df = self.party_rank()

        if df.empty:
            return df

        # df = raw.copy()
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

    def get_total(self) -> Dict:

        self.check_set_d()
        raw = self.tx.raw_by_direction(self.d)
        workdays = (self.tx.end_time - self.tx.start_time).days + 1

        insts = raw[C.INST_DAYS].sum()
        avg_amt = raw[C.PRODUCT].sum() / workdays
        products = raw[C.PRODUCT].sum()

        rate = insts * self.tx.inst_base / products * 100 if products != 0 else 0

        return {
            'avg_amt': avg_amt,
            'insts': insts,
            'rate': rate
        }

    def add_total(self, raw: pd.DataFrame, flag: int = 1) -> pd.DataFrame:
        """
        添加“合计”行到原数据.

        原数据格式：[C.NAME, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE]

        Args:
            raw (pd.DataFrame): 要添加的源数据.
            flag (int): 1, 添加到最后一行.  0, 添加到第一行.

        Returns:
            pd.DataFrame: [C.NAME, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE]
        """

        # flag为1时，合计在最后，为0时，合计在最前

        if raw.empty:
            return raw

        # df = raw.copy()
        rate_total = raw[C.INST_GROUP].sum() * self.tx.inst_base / raw[C.PRODUCT].sum() * 100 \
            if raw[C.PRODUCT].sum() != 0 else 0

        total = {
            raw.columns[0]: '合计',
            C.AVG_AMT: raw[C.AVG_AMT].sum(),
            C.INST_GROUP: raw[C.INST_GROUP].sum(),
            C.PRODUCT: raw[C.PRODUCT].sum(),
            C.WEIGHT_RATE: rate_total
        }
        if flag == 1:
            return pd.concat([raw, pd.DataFrame([total])]).reset_index(drop=True)
        else:
            return pd.concat([pd.DataFrame([total]), raw]).reset_index(drop=True)

    def term_rank(self) -> pd.DataFrame:
        """
        按照各期限的日均余额进行排名，返回统计数据.

        :arg
            d (int): 交易方向，资金融入为4，资金融出为1

        Returns:
            pd.DataFrame: [C.TERM_TYPE, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE]
        """

        self.check_set_d()

        if self.tx.raw_by_direction(self.d).empty:
            return pd.DataFrame({})

        term = self.tx.groupby_column(C.TERM_TYPE, self.d)

        return term

    def head_stats(self) -> Dict:
        """
        统计交易数据，用于在资金交易页面的题头显示.

        Returns:
            Dict: {C.TRADE_NUM, C.TRADE_SUM, C.TRADE_WEIGHT_SUM, C.MAX_RATE, C.MIN_RATE}
        """

        self.check_set_d()

        raw = self.tx.raw_by_direction(self.d)

        if raw.empty:
            return {}

        mask = ((raw[C.SETTLEMENT_DATE] >= self.tx.start_time.strftime('%Y-%m-%d')) &
                (raw[C.SETTLEMENT_DATE] <= self.tx.end_time.strftime('%Y-%m-%d')))

        occ_stats = raw[mask]

        return {
            # 交易笔数
            C.TRADE_NUM: occ_stats.shape[0],
            # 交易总额（按发生）
            C.TRADE_SUM: occ_stats[C.TRADE_AMT].sum(),
            # 交易金额（按加权）
            C.TRADE_WEIGHT_SUM: raw[C.TRADE_AMT].sum(),
            # 单笔利率(最大）
            C.MAX_RATE: occ_stats[C.RATE].max(),
            # 单笔利率(最小）
            C.MIN_RATE: occ_stats[C.RATE].min()
        }

    @staticmethod
    def format_output(raw: pd.DataFrame) -> pd.DataFrame:
        """
        格式化输出的 DataFrame。
        1. 将索引加 1。
        2. 格式化平均金额、同业利率和加权利率列。

        Args:
            raw (pd.DataFrame): 被格式化的df. 列需包含[C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]

        Returns:
            pd.DataFrame: df.
        """

        raw.index = raw.index + 1
        raw[C.AVG_AMT] = raw[C.AVG_AMT].map('{:,.2f}'.format)
        raw[C.INST_GROUP] = raw[C.INST_GROUP].map('{:,.2f}'.format)
        raw[C.WEIGHT_RATE] = raw[C.WEIGHT_RATE].map('{:.4f}'.format)

        return raw

    def all_data_show(self) -> Dict:
        """
        获取各类统计信息，方便资金交易页面显示。

        该方法检索各种交易数据和统计信息，包括持有数据、交易对手排名、期限排名和发生统计。
        然后将这些数据打包成一个字典并返回。

        返回的字典包括以下内容:

        - 'holded': 每日持仓.

        - 'party': 按主机构排名.

        - 'party_total': 按主机构排名（添加了“合计”行).

        - 'party_n': 按主机构排名（前n+其他).

        - 'partyn_total': 按主机构排名（前n+其他+合计)

        - 'term': 期限排名

        - 'term_total': 期限排名（添加“合计"行）

        - 'occ': 其他统计数据.


        Returns:
            Dict: 字典形式的统计数据.
        """

        self.check_set_d()

        txn_daily = self.daily_data()
        txn_party = self.party_rank()
        txn_party_total = self.add_total(txn_party, 1)
        txn_party_n = self.party_rank_n()
        txn_partyn_total = self.add_total(txn_party_n, 0)
        txn_term = self.term_rank()
        txn_term_total = self.add_total(txn_term, 1)
        txn_occ = self.head_stats()

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

    def monthly_summary(self, mark_rate: float = 0) -> pd.DataFrame:
        """
        按月度分组，返回月度统计数据

        注意：内部对象FundTx的统计截至时间为当前时间的前一天

        :param mark_rate: 用于计算套息的基准利率
        :return: [C.DATE, C.TYPE, C.AVG_AMT, C.INST_DAYS, C.INST_GROUP, C.WEIGHT_RATE, C.RATE]
        """

        # start_time = self.tx.get_stime()
        start_time = self.tx.start_time
        inst_base = self.tx.inst_base

        self.check_set_d()

        dh = self.tx.daily_data(self.d)

        # 如果无交易，则返回一个都为0的df
        if dh.empty:
            months = TimeUtil.get_months_feday(start_time.year)
            # print(months)

            # 生成一个包含每个月最后一天的日期索引的DataFrame
            dates = pd.to_datetime([end for _, end in months])
            df = pd.DataFrame(index=dates, columns=[C.TX_TYPE, C.AVG_AMT, C.WORK_DAYS, C.INST_DAYS,
                                                    C.INST_GROUP, C.WEIGHT_RATE, C.RATE])

            df[C.TX_TYPE] = ''
            df[[C.AVG_AMT, C.WORK_DAYS, C.INST_DAYS, C.INST_GROUP, C.WEIGHT_RATE, C.RATE]] = 0
            df.index.name = C.DATE
            # print(df)

            return df

        dh.rename(columns={C.TRADE_AMT: C.AVG_AMT}, inplace=True)
        dh.set_index(C.AS_DT, inplace=True)

        # 按月末进行汇总
        dh_monthly = dh.resample('ME').sum()
        workdays = dh_monthly.index.days_in_month

        # 计算月均余额
        dh_monthly[C.AVG_AMT] = dh_monthly[C.AVG_AMT] / workdays
        # 计算月均加权利率
        dh_monthly[C.WEIGHT_RATE] = (dh_monthly[C.INST_DAYS] * inst_base / workdays /
                                     dh_monthly[C.AVG_AMT]) * 100

        # 重置为0，方便下面的计算
        dh_monthly.loc[:, [C.INST_GROUP, C.RATE]] = 0.0

        if self.d == 4:
            # 计算套息收入
            dh_monthly[C.INST_GROUP] = (dh_monthly[C.AVG_AMT] * (mark_rate - dh_monthly[C.WEIGHT_RATE]) /
                                        100 * workdays / inst_base)
            dh_monthly[C.RATE] = mark_rate - dh_monthly[C.WEIGHT_RATE]

        last_row = dh_monthly.iloc[-1]
        current_date = datetime.now()

        # 如果是当前年，则要对最后一行的日均余额进行处理，否则会以最后一个月的所有天数计算
        if last_row.name.year == current_date.year and last_row.name.month == current_date.month:
            # Calculate the number of days from the start of the month to the previous day
            start_of_month = datetime(current_date.year, current_date.month, 1)

            # 重新按实际统计天数计算相关列
            # 计算日均余额
            days_interval = ((current_date - timedelta(days=1)).day - start_of_month.day + 1)
            avg_amt_loc = dh_monthly.columns.get_loc(C.AVG_AMT)
            weight_rate_loc = dh_monthly.columns.get_loc(C.WEIGHT_RATE)
            inst_group_loc = dh_monthly.columns.get_loc(C.INST_GROUP)

            dh_monthly.iloc[-1, avg_amt_loc] = dh_monthly.iloc[-1, avg_amt_loc] / days_interval

            # 计算加权利率
            if dh_monthly.iloc[-1, avg_amt_loc] != 0:
                dh_monthly.iloc[-1, weight_rate_loc] = ((dh_monthly.iloc[-1][C.INST_DAYS] * inst_base / days_interval /
                                                         dh_monthly.iloc.iloc[-1, avg_amt_loc]) * 100)

            # 计算套息收入
            if self.d == 4:
                dh_monthly.iloc[-1, inst_group_loc] = (
                        dh_monthly.iloc[-1][C.AVG_AMT] * (mark_rate - dh_monthly.iloc[-1][C.WEIGHT_RATE])
                        / 100 * days_interval / inst_base)

                dh_monthly.iloc[-1, dh_monthly.columns.get_loc(C.RATE)] = mark_rate - dh_monthly.iloc[-1][C.WEIGHT_RATE]

        dh_monthly[C.TX_TYPE] = ''
        dh_monthly.loc[dh_monthly[C.INST_DAYS] == 0, [C.WEIGHT_RATE, C.INST_GROUP, C.RATE]] = 0.0

        dh_monthly = dh_monthly[[C.TX_TYPE, C.AVG_AMT, C.INST_DAYS, C.INST_GROUP, C.WEIGHT_RATE, C.RATE]].rename_axis(
            C.DATE)

        return dh_monthly


class SecurityDataHandler:
    """
    处理固收交易数据的工具类。

    Attributes
    ----------
    tx : SecurityTx
        固收交易对象.
    raw : pd.DataFrame
        区间内收益相关数据.
    inst_rate_bond : set
        利率债代码集.
    """

    def __init__(self, txn: SecurityTx) -> None:
        """
        构建函数.

        Parameters
        ----------
            txn : 固收交易对象
        """
        self.tx = txn
        self.raw = self.tx.get_all_daily_profit()

        # 利率债的sectype
        self.inst_rate_bond = {0, 1, 6, 11}

    def get_holding_bonds_endtime(self) -> pd.DataFrame:
        """
        返回在统计区间末时点的持有债券数据
        :return: [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE,
        C.BOND_TYPE_NUM, C.BOND_TYPE, C.COUPON_RATE_ISSUE, C.COUPON_RATE_CURRENT, C.ISSUE_AMT, C.ISSUE_PRICE,
        C.ISSUE_ORG, C.MATURITY]
        """

        holded = self.tx.holded[self.tx.holded[C.DATE].dt.date == self.tx.end_time]
        # bond_info = self.tx.holded_bonds_info[self.tx.holded_bonds_info[C.DATE].dt.date == self.tx.end_time]
        bond_info = self.tx.holded_bonds_info

        # print(bond_info)

        if bond_info.empty:
            return pd.DataFrame({})

        holded = pd.merge(holded, bond_info[[C.BOND_CODE, C.BOND_TYPE, C.COUPON_RATE_ISSUE, C.COUPON_RATE_CURRENT,
                                             C.ISSUE_AMT, C.ISSUE_PRICE, C.ISSUE_ORG, C.MATURITY]],
                          on=C.BOND_CODE,
                          how='left')

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(holded)

        return holded

    def get_all_trades(self) -> pd.DataFrame:
        """
        返回所有交易数据

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_CODE, C.BOND_NAME, C.MARKET_CODE, C.DIRECTION, C.BOND_AMT_CASH, C.NET_PRICE,
            C.ACCRUED_INST_CASH, C.TRADE_AMT, C.SETTLE_AMT, C.TRADE_TYPE, C.FULL_PRICE]
        """
        # primary_trades = self.tx.get_primary_trades()
        primary_trades = self.tx.primary_trades
        secondary_trades = self.tx.secondary_trades

        if primary_trades.empty and secondary_trades.empty:
            return pd.DataFrame({})

        primary_trades[C.TRADE_TYPE] = '一级'
        secondary_trades[C.TRADE_TYPE] = '二级'

        if primary_trades.empty:
            all_trades = secondary_trades
        elif secondary_trades.empty:
            all_trades = primary_trades
        else:
            all_trades = pd.concat([secondary_trades, primary_trades], ignore_index=True)

        # 对于一级交易，补全要素以保持格式一致
        mask = all_trades[C.TRADE_TYPE] == '一级'
        # 结算金额
        all_trades.loc[mask, C.SETTLE_AMT] = all_trades.loc[mask, C.NET_PRICE] * all_trades.loc[
            mask, C.BOND_AMT_CASH] / 100
        all_trades.loc[mask, C.FULL_PRICE] = all_trades.loc[mask, C.NET_PRICE]
        all_trades.loc[mask, C.ACCRUED_INST_CASH] = 0
        all_trades.loc[mask, C.TRADE_AMT] = all_trades.loc[mask, C.SETTLE_AMT]
        # all_trades.loc[mask, C.TRADE_AMT] = all_trades.loc[mask, C.NET_PROFIT]

        mask = all_trades[C.DIRECTION] == 1

        # Ensure the column is of type object (string) before assignment
        all_trades[C.DIRECTION] = all_trades[C.DIRECTION].astype(str)

        all_trades.loc[mask, C.DIRECTION] = '买入'
        all_trades.loc[~mask, C.DIRECTION] = '卖出'

        all_trades.drop(columns=[C.BOND_TYPE_NUM], inplace=True)

        # print(all_trades)

        return all_trades

    def monthly_summary(self) -> pd.DataFrame:
        """
        按月度分组，返回统计数据，用于“主页”显示

        注意：内部对象FundTx的统计截至时间为当前时间的前一天

        :return: df[C.DATE, C.AVG_AMT, C.INST_DAYS, C.CAPITAL_GAINS, C.WEIGHT_RATE]，这里的收益率是不含净价浮盈的
        """

        start_time = self.tx.start_time
        end_time = self.tx.end_time

        # print(start_time)
        # print(end_time)

        dh = self.daily_yield_all_cum(start_time, end_time)
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(dh)
        # print(dh)

        # 如果为空，仍然要返回带格式的df
        if dh.empty:
            months = TimeUtil.get_months_feday(start_time.year)

            # 生成一个包含每个月最后一天的日期索引的DataFrame
            dates_index = pd.to_datetime([end for _, end in months])

            df = pd.DataFrame(index=dates_index, columns=[C.AVG_AMT, C.INST_DAYS, C.CAPITAL_GAINS, C.WEIGHT_RATE])
            df[[C.AVG_AMT, C.INST_DAYS, C.CAPITAL_GAINS, C.WEIGHT_RATE]] = 0

            df.index.name = C.DATE

            return df

        dh.set_index(C.DATE, inplace=True)

        dh_monthly = dh.resample('ME').sum()
        # print(dh_monthly)

        month_end_dates = pd.date_range(start=start_time, end=end_time, freq='ME')
        # 使用 reindex 补全每月最后一天并填充 0
        dh_monthly = dh_monthly.reindex(dh_monthly.index.union(month_end_dates).sort_values(), fill_value=0)

        # 计算月均持仓面额
        dh_monthly[C.AVG_AMT] = dh_monthly[C.HOLD_AMT] / dh_monthly.index.days_in_month

        # 计算月均加权收益率
        dh_monthly[C.WEIGHT_RATE] = ((dh_monthly[C.INST_A_DAY] * 365 +
                                      dh_monthly[C.CAPITAL_GAINS] * dh_monthly.index.days_in_month) /
                                     dh_monthly[C.CAPITAL_OCCUPY]) * 100

        # 无收益的情况，直接置为0
        dh_monthly.loc[(dh_monthly[C.INST_A_DAY] + dh_monthly[C.CAPITAL_GAINS]) == 0, C.WEIGHT_RATE] = 0

        last_row = dh_monthly.iloc[-1]
        current_date = datetime.now()

        # 如果是当前年，则要对最后一行的实际天数进行计算，否则会统计所有天数
        if last_row.name.year == current_date.year and last_row.name.month == current_date.month:
            # 计算当前年当前月的实际天数
            start_of_month = datetime(current_date.year, current_date.month, 1)
            days_interval = ((current_date - timedelta(days=1)).day - start_of_month.day + 1)

            # 重新按实际统计天数计算日均余额列
            avg_amt = dh_monthly.columns.get_loc(C.AVG_AMT)
            dh_monthly.iloc[-1, avg_amt] = dh_monthly.iloc[-1, avg_amt] / days_interval

            # 如果日均余额非0， 还要更新加权利率
            if dh_monthly.iloc[-1, avg_amt] != 0:
                dh_monthly.iloc[-1, dh_monthly.columns.get_loc(C.WEIGHT_RATE)] = \
                    ((dh_monthly.iloc[-1][C.INST_A_DAY] * 365 + dh_monthly.iloc[-1][C.CAPITAL_GAINS] * days_interval) /
                     dh_monthly.iloc[-1][C.CAPITAL_OCCUPY]) * 100

        # 对列重命名，统一格式
        dh_monthly = dh_monthly[[C.AVG_AMT, C.INST_A_DAY, C.CAPITAL_GAINS, C.WEIGHT_RATE]].rename(
            columns={C.INST_A_DAY: C.INST_DAYS}).rename_axis(C.DATE)

        return dh_monthly

    def daily_yield_all(self) -> pd.DataFrame:

        """
        统计区间内全部债券每日收益情况（非累加）

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.YIELD, YIELD_NO_NET_PROFIT]
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw)

        return raw_group

    def daily_yield_inst_rate_bond(self) -> pd.DataFrame:

        """
        统计区间内利率债每日收益情况（非累加）

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.YIELD, YIELD_NO_NET_PROFIT]
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw[self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def daily_yield_credit_bond(self) -> pd.DataFrame:

        """
        统计区间内信用债每日收益情况（非累加）

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.YIELD, YIELD_NO_NET_PROFIT]
        """

        if self.raw.empty:
            return pd.DataFrame({})

        raw_group = self.cal_daily_yield(self.raw[~self.raw[C.BOND_TYPE_NUM].isin(self.inst_rate_bond)])

        return raw_group

    def _yield_cum_by(self, start_time: datetime.date, end_time: datetime.date, by_type: str) -> List[pd.DataFrame]:
        """
        按by_type（如C.BOND_CODE)分类，计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :param by_type: 分组类型
        :return: [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.COST_FULL_PRICE, COST_NET_PRICE, C.BOND_TYPE, C.VALUE_NET_PRICE
            C.ISSUE_ORG, C.INST_DAYS, C.CAPITAL_GAINS_CUM, C.NET_PROFIT_SUB, C.TOTAL_PROFIT_CUM, CAPITAL_OCCUPY_CUM
            C.WORK_DAYS, C.YIELD_CUM]
        """

        # 持有债券的基础信息
        bonds_info = self.tx.holded_bonds_info
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

            # 重要：由于_cal_daily_yield_cum要求日期项不能重复，先用groupby按日期聚合
            bond = bond.groupby(C.DATE).agg(agg_dict)
            # 分组数据计算后形成列表
            bond_list.append(self.cal_daily_yield_cum(bond, start_time, end_time, 1))

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(bond_list)

        return bond_list

    def yield_cum_by_code(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        按债券代码(C.BOND_CODE)分组,计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :return:
            [C.BOND_CODE, C.BOND_NAME, C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
            C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]
        """

        bond_list = self._yield_cum_by(start_time, end_time, C.BOND_CODE)

        return self.yield_data_format(bond_list, start_time, end_time, [C.BOND_CODE, C.BOND_NAME])

    def yield_cum_by_market(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:
        """
        按市场代码(C.MARKET_CODE)分组,计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :return:
            [C.MARKET_CODE, C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
            C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]
        """

        bond_list = self._yield_cum_by(start_time, end_time, C.MARKET_CODE)

        return self.yield_data_format(bond_list, start_time, end_time, [C.MARKET_CODE])

    def yield_cum_by_org(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:
        """
        按发行人(C.ISSUE_ORG)分组,计算每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :return:
            [C.ISSUE_ORG, C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
            C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]
        """
        bond_list = self._yield_cum_by(start_time, end_time, C.ISSUE_ORG)

        return self.yield_data_format(bond_list, start_time, end_time, [C.ISSUE_ORG])

    def daily_yield_all_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

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
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.COST_FULL_PRICE, COST_NET_PRICE, C.BOND_TYPE, C.VALUE_NET_PRICE
            C.ISSUE_ORG, C.INST_DAYS, C.CAPITAL_GAINS_CUM, C.NET_PROFIT_SUB, C.TOTAL_PROFIT_CUM, CAPITAL_OCCUPY_CUM
            C.WORK_DAYS, C.YIELD_CUM]
        """

        return self.cal_daily_yield_cum(self.daily_yield_all(), start_time, end_time, 1)

    def daily_yield_inst_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        按天数聚合<利率债>每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，

        Parameters
        ----------
        start_time : datetime.date
            开始时间
        end_time : datetime.date
            结束时间

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.COST_FULL_PRICE, COST_NET_PRICE, C.BOND_TYPE, C.VALUE_NET_PRICE
            C.ISSUE_ORG, C.INST_DAYS, C.CAPITAL_GAINS_CUM, C.NET_PROFIT_SUB, C.TOTAL_PROFIT_CUM, CAPITAL_OCCUPY_CUM
            C.WORK_DAYS, C.YIELD_CUM]
        """

        return self.cal_daily_yield_cum(self.daily_yield_inst_rate_bond(), start_time, end_time, 1)

    def daily_yield_credit_cum(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        按天数聚合<信用债>每日资金占用，资本利得，净价浮盈，利息收入等收益相关数据的累计值，

        Parameters
        ----------
        start_time : datetime.date
            开始时间
        end_time : datetime.date
            结束时间

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.COST_FULL_PRICE, COST_NET_PRICE, C.BOND_TYPE, C.VALUE_NET_PRICE
            C.ISSUE_ORG, C.INST_DAYS, C.CAPITAL_GAINS_CUM, C.NET_PROFIT_SUB, C.TOTAL_PROFIT_CUM, CAPITAL_OCCUPY_CUM
            C.WORK_DAYS, C.YIELD_CUM]
        """

        return self.cal_daily_yield_cum(self.daily_yield_credit_bond(), start_time, end_time, 1)

    # 1.1 保留单日收益率计算，留以后结合负债做收益计算
    @staticmethod
    def cal_daily_yield(bond_data: pd.DataFrame) -> pd.DataFrame:

        """
        按单日C.DATE进行聚合，计算单日资金占用，资本利得，净价浮盈，利息收入等收益相关数据

        Parameters
        ----------
        bond_data : pd.DataFrame
            要统计的数据集.

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.YIELD, YIELD_NO_NET_PROFIT]
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

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw_group)

        return raw_group

    @staticmethod
    def cal_daily_yield_cum(bonds_data: pd.DataFrame, start_time: datetime.date, end_time: datetime.date,
                            flag_net: int = 1) -> pd.DataFrame:
        """
        计算每日资金占用，资本利得，净价浮盈，利息收入，总收益和每日收益率等收益情况的累计值。注意：单日数据不能有重复值（不能存在多个相同日期），
        默认包含净价浮盈，可设置flag_net为0不包含
        :param flag_net: 默认为1，包含净价浮盈，为0则不包含
        :param bonds_data:
            要计算的每日债券收益数据：
            包含[C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY,
            C.NET_PROFIT, C.TOTAL_PROFIT,C.YIELD, YIELD_NO_NET_PROFIT]
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :return:
            [C.DATE, C.HOLD_AMT, C.CAPITAL_OCCUPY, C.CAPITAL_GAINS, C.INST_A_DAY, C.NET_PROFIT, C.TOTAL_PROFIT,
            C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.COST_FULL_PRICE, COST_NET_PRICE, C.BOND_TYPE, C.VALUE_NET_PRICE
            C.ISSUE_ORG, C.INST_DAYS, C.CAPITAL_GAINS_CUM, C.NET_PROFIT_SUB, C.TOTAL_PROFIT_CUM, CAPITAL_OCCUPY_CUM
            C.WORK_DAYS, C.YIELD_CUM]
        """

        if bonds_data.empty:
            return pd.DataFrame({})

        # 生成一个时间序列
        date_range = pd.date_range(start=start_time, end=end_time)
        df_empty = pd.DataFrame(date_range, columns=[C.DATE])

        daily_data_cum = pd.merge(df_empty, bonds_data, on=C.DATE, how='left')

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        # 在统计时间区间内，存在一开始就没有数据的情况，需要对这些日期进行填充
        first_valid_index = daily_data_cum[C.HOLD_AMT].first_valid_index()
        # 如果第一个非空行不是第一行，将第一行至首个非空值（不包含）间的行赋值为首个非空行的值
        if first_valid_index != daily_data_cum.index[0]:
            first_valid_row = daily_data_cum.loc[first_valid_index]
            last_invaid_index = first_valid_index - 1

            # 除固定列外，对于其他列，将它们的值设置为首个非空行的值

            # 获取需要修改的列（排除固定列）
            columns_to_update = daily_data_cum.columns.difference(
                [C.DATE, C.HOLD_AMT, C.INST_A_DAY, C.CAPITAL_GAINS, C.NET_PROFIT, C.CAPITAL_OCCUPY, C.TOTAL_PROFIT,
                 C.COST_NET_PRICE]
            )

            # 将指定范围的列值设置为首个非空行的值
            daily_data_cum.loc[:last_invaid_index, columns_to_update] = first_valid_row[columns_to_update].values

            # for column in daily_data_cum.columns:
            #     if column not in [C.HOLD_AMT, C.INST_A_DAY, C.CAPITAL_GAINS, C.NET_PROFIT, C.CAPITAL_OCCUPY,
            #                       C.TOTAL_PROFIT, C.COST_NET_PRICE]:
            #         daily_data_cum.loc[:last_invaid_index, column] = first_valid_row[column]

            # 将第一行至首个非空值的某些行（不包含）间的行赋值为0
            daily_data_cum.loc[:last_invaid_index, [C.HOLD_AMT, C.CAPITAL_OCCUPY, C.COST_NET_PRICE,
                                                    C.COST_FULL_PRICE, C.TOTAL_PROFIT]] = 0.0

        # ----- 填充完毕 ------
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)
        # 计算累计利息收入
        # daily_data_cum[C.INST_A_DAY] = daily_data_cum[C.INST_A_DAY].infer_objects(copy=False).fillna(0.0)
        daily_data_cum[C.INST_A_DAY] = daily_data_cum[C.INST_A_DAY].fillna(0.0)
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

        # 如果不包含净价浮盈，将净价浮盈列设置为0
        if flag_net == 0:
            daily_data_cum.loc[:, C.NET_PROFIT_SUB] = 0

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
        # TODO 同业存单计算方式不同，后期待优化
        daily_data_cum[C.YIELD_CUM] = ((daily_data_cum[C.INST_DAYS] * 365 /
                                        daily_data_cum[C.WORK_DAYS] + daily_data_cum[C.CAPITAL_GAINS_CUM] +
                                        daily_data_cum[C.NET_PROFIT_SUB]) /
                                       (daily_data_cum[C.CAPITAL_OCCUPY_CUM] /
                                        daily_data_cum[C.WORK_DAYS]) * 100)

        daily_data_cum = daily_data_cum.ffill()
        daily_data_cum = daily_data_cum.fillna(0)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily_data_cum)

        return daily_data_cum

    @staticmethod
    def yield_data_format(raw_data: List[pd.DataFrame], start_time: datetime.date, end_time: datetime.date,
                          columns_ro: List[str]) -> pd.DataFrame:
        """
        将收益数据格式化，更好的展示到web页面上
        :param raw_data: 收益数据的集合，每个元素为一个DataFrame，每个DataFrame为一个分组的收益数据
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :param columns_ro: 该组列仅展示，无需做数值计算，取每列的第一行数据
        :return:
            [[columns_ro], C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB, C.CAPITAL_GAINS,
            C.TOTAL_PROFIT_CUM, C.YIELD_CUM]
        """

        # 创建一个空的DataFrame， columns包含了要展示的列
        df = pd.DataFrame(columns=(columns_ro + [C.AVG_AMT, C.CAPITAL_OCCUPY, C.INTEREST_AMT, C.NET_PROFIT_SUB,
                                                 C.CAPITAL_GAINS, C.TOTAL_PROFIT_CUM, C.YIELD_CUM]))

        i = 0
        count_days = (end_time - start_time).days + 1

        for raw in raw_data:

            if raw.empty:
                continue
            insts = raw.iloc[-1][C.INST_DAYS]
            capital_gains = raw[C.CAPITAL_GAINS].sum()
            net_profit = raw.iloc[-1][C.NET_PROFIT_SUB]

            temp = []

            for column in columns_ro:
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


class OverviewDataHandler:
    """
    按年统计所有交易数据的类，包括资金交易和固收交易。
    主要用于主页的环比，同比统计
    """

    def __init__(self, year_num: int):
        """
        构造函数
        :param year_num: 年份
        """

        self.tx_data_dict = {}

        self.y = year_num
        self.tx_total_dict = {}

    def fund_monthly_report_yoy(self, tx_type: Union[C.REPO, C.REPL, C.IBO, C.IBL], mark_rate: float = 0,
                                mark_rate_p: float = 0) -> DataFrame:
        """
        生成资金交易year_num年和前一年的月度报告，用于测算同比。

        该函数根据指定的年份、交易类型和方向创建一个交易对象，然后基于提供的基准利率生成该年各月的统计情况。

        Args:
            tx_type (str): 四种类型C.REPO, C.REPL, C.IBO, C.IBL。
            mark_rate (float, optional): 基准年份的测算利率，用于计算套利收入的基准利率，默认为 0。
            mark_rate_p (float, optional): 基准年份前一年的测算利率，默认为 0。

        Returns:
            pd.DataFrame: 包含月度汇总报告的 DataFrame，列包括:
                          [C.DATE, C.AVG_AMT, C.INST_DAYS, C.INST_GROUP, C.WEIGHT_RATE, C.TX_TYPE, [前面数值列名+'_P']]
        """

        # 如果已经测算过，直接返回
        if self.tx_data_dict.get(tx_type) is not None:
            return self.tx_data_dict[tx_type]

        # 计算当期的报告
        current = self.fund_monthly_report(self.y, tx_type, mark_rate)[0]
        # 计算前期的报告
        previous = self.fund_monthly_report(self.y - 1, tx_type, mark_rate_p)[0]

        # 创建包含月份的列，以便按月份进行匹配
        current['Month'] = current.index.month
        previous['Month'] = previous.index.month

        current = current.reset_index()

        merged_df = pd.merge(current, previous, on='Month', suffixes=('', '_P'), how='left').drop(columns=['Month'])
        merged_df = merged_df.set_index(C.DATE)

        merged_df.drop(columns=[C.TX_TYPE + '_P'], inplace=True)

        mask = merged_df[C.INST_DAYS + '_P'] != 0
        merged_df[C.INST_DAYS + C.YOY] = 0.0
        merged_df.loc[mask, C.INST_DAYS + C.YOY] = ((merged_df.loc[mask, C.INST_DAYS] -
                                                     merged_df.loc[mask, C.INST_DAYS + '_P']) /
                                                    merged_df.loc[mask, C.INST_DAYS + '_P'] * 100)

        self.tx_data_dict[tx_type] = merged_df

        return merged_df

    def fund_monthly_report(self, year: int, tx_type: Union[C.REPO, C.REPL, C.IBO, C.IBL],
                            mark_rate: float = 0) -> List:
        """
        生成资金交易的月度报告。

        该函数根据指定的年份、交易类型和方向创建一个交易对象，然后基于提供的基准利率生成该年各月的统计情况。

        Args:
            year (int): 年份
            tx_type (str): 四种类型C.REPO, C.REPL, C.IBO, C.IBL。。
            mark_rate (float, optional): 用于计算套利收入的基准利率，默认为 0。

        Returns:
            pd.DataFrame: 包含月度汇总报告的 Dict，列包括:
                          [C.DATE, C.TYPE, C.AVG_AMT, C.INST_DAYS, C.INST_GROUP, C.WEIGHT_RATE]
        """

        if tx_type not in [C.REPO, C.REPL, C.IBO, C.IBL]:
            return [pd.DataFrame({}), pd.DataFrame({})]

        months = TimeUtil.get_months_feday(year)

        start_time = months[0][0]
        end_time = months[-1][1]

        txn = None

        if tx_type in [C.REPO, C.REPL]:
            txn = TxFactory(Repo).create_txn(start_time, end_time)

        if tx_type in [C.IBO, C.IBL]:
            txn = TxFactory(IBO).create_txn(start_time, end_time)

        tx_hl = FundDataHandler(txn)
        tx_hl.set_direction(tx_type)

        tx_data = tx_hl.monthly_summary(mark_rate)
        tx_data[C.TX_TYPE] = tx_type

        # 计算合计值
        total = tx_hl.get_total()
        work_days = (end_time - start_time).days + 1
        total['insts_other'] = 0

        if tx_type in [C.REPO, C.IBO]:
            total['insts_other'] = total['avg_amt'] * (mark_rate - total['rate']) * work_days / txn.inst_base / 100
        self.tx_total_dict[tx_type + str(year)] = total

        return [tx_data, total]

    # def create_fundtx(self, direction: str) -> None:

    def get_tx_total(self, tx_type: str, year: int) -> Dict:
        total = self.tx_total_dict.get(tx_type + str(year))
        return total if total is not None else {}

    def security_monthly_report(self, tx_type: Union[C.BOND, C.CD]) -> pd.DataFrame:
        """
        生成固收交易的月度报告。

        该函数根据指定的年份、交易类型创建一个交易对象，生成该年各月的统计情况。

        Args:
            tx_type (str): 交易类型，C.BOND或C.CD。

        Returns:
            pd.DataFrame: 包含月度汇总报告的 DataFrame，列包括:
                          [C.DATE, C.AVG_AMT, C.INST_DAYS, C.CAPITAL_GAINS, C.WEIGHT_RATE]，收益率是不含净价浮盈的
        """
        months = TimeUtil.get_months_feday(self.y)
        start_time = months[0][0]
        # print(start_time)
        end_time = months[-1][1]

        if tx_type == C.BOND:
            txn_type = BondTx
        elif tx_type == C.CD:
            txn_type = CDTx
        else:
            return pd.DataFrame({})

        txn_data = SecurityDataHandler(txn_type(start_time, end_time)).monthly_summary()
        txn_data[C.TX_TYPE] = tx_type

        # txn_data.index.name = C.DATE

        return txn_data

    def security_monthly_report_yoy(self, tx_type: Union[C.BOND, C.CD]) -> pd.DataFrame:
        """
        生成固收交易year_num年和前一年的月度报告，用于测算同比。

        Args:
            tx_type (str): 交易类型，C.BOND或C.CD。

        Returns:
            pd.DataFrame: 包含月度报告的 DataFrame，列包括:
                          [C.DATE, C.AVG_AMT, C.INST_DAYS, C.CAPITAL_GAINS, C.WEIGHT_RATE,C.TX_TYPE, [前面数值列名+'_P']]
        """

        if self.tx_data_dict.get(tx_type) is not None:
            return self.tx_data_dict[tx_type]

        current = self.security_monthly_report(tx_type)
        self.y -= 1

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(current)

        previous = self.security_monthly_report(tx_type)
        self.y += 1

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(previous)

        # 如果任意一个为空，则添加列后返回
        # if current.empty or previous.empty:
        #     cols = [col + '_P' for col in current.columns]
        #     current.loc[:, cols] = 0
        #     return current

        # 创建包含月份的列，以便按月份进行匹配
        current['Month'] = current.index.month

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(current)

        previous['Month'] = previous.index.month
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(previous)

        current = current.reset_index()

        merged_df = pd.merge(current, previous, on='Month', suffixes=('', '_P'), how='left').drop(columns=['Month'])

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(merged_df)

        merged_df = merged_df.set_index(C.DATE)

        merged_df.drop(columns=[C.TX_TYPE + '_P'], inplace=True)

        # for col in current_cols:
        #     # print(col)
        #     merged_df[col + C.YOY] = ((merged_df[col] - merged_df[col + '_P']) /
        #                               merged_df[col + '_P'] * 100)

        merged_df[C.TOTAL_PROFIT] = merged_df[C.INST_DAYS] + merged_df[C.CAPITAL_GAINS]
        merged_df[C.TOTAL_PROFIT + '_P'] = merged_df[C.INST_DAYS + '_P'] + merged_df[C.CAPITAL_GAINS + '_P']

        mask = merged_df[C.TOTAL_PROFIT + '_P'] != 0
        merged_df[C.TOTAL_PROFIT + C.YOY] = 0.0
        merged_df.loc[mask, C.TOTAL_PROFIT + C.YOY] = ((merged_df.loc[mask, C.TOTAL_PROFIT] -
                                                        merged_df.loc[mask, C.TOTAL_PROFIT + '_P']) /
                                                       merged_df.loc[mask, C.TOTAL_PROFIT + '_P'] * 100)

        merged_df[C.WEIGHT_RATE + '_SUB'] = (merged_df[C.WEIGHT_RATE] - merged_df[C.WEIGHT_RATE + '_P']) * 100

        self.tx_data_dict[tx_type] = merged_df

        return merged_df

    def asset_debt_data(self) -> pd.DataFrame:
        """
        生成资产负债的收入或支出数据
        :return: [C.TX_TPYE, C.TOTAL_PROFIT]
        """

        tx_types = [C.REPL, C.IBL, C.BOND, C.CD, C.REPO, C.IBO]

        data = pd.DataFrame(columns=[C.TX_TYPE, C.TOTAL_PROFIT])

        for tx_type in tx_types:

            new_row = pd.DataFrame({C.TX_TYPE: [tx_type], C.TOTAL_PROFIT: [0.0]})

            if self.tx_data_dict.get(tx_type) is None:
                if tx_type in [C.REPL, C.IBL, C.REPO, C.IBO]:
                    self.fund_monthly_report_yoy(tx_type)
                elif tx_type in [C.BOND, C.CD]:
                    self.security_monthly_report_yoy(tx_type)
                else:
                    raise ValueError('Unknown tx_type')

            if tx_type in [C.REPL, C.IBL, C.REPO, C.IBO]:
                new_row[C.TOTAL_PROFIT] = self.tx_data_dict[tx_type][C.INST_DAYS].sum()
            elif tx_type in [C.BOND, C.CD]:
                new_row[C.TOTAL_PROFIT] = self.tx_data_dict[tx_type][C.TOTAL_PROFIT].sum()
            else:
                raise ValueError('Unknown tx_type')

            if data.empty:
                data = new_row
            else:
                data = pd.concat([data, new_row], ignore_index=True)

        return data


if __name__ == '__main__':
    # dh = fundtx_monthly_report(2023, IBO, '同业拆入', 2)
    # dh = security_monthly_report(2023, BondTx)
    # dh = fundtx_monthly_report(2023, Repo, '正回购', 1.8)

    print('xx')
