# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond_tx
# Description: This module contains classes for handling security transactions, specifically for bonds and CDs.
import datetime
import pandas as pd

from utils.db_util import get_raw, create_conn
from utils.db_util import Constants as C


class SecurityTx:
    """
        固定收益业务的基类.

        ...

        Attributes
        ----------
        start_time : datetime.date
            交易开始统计时间
        end_time : datetime.date
            交易截至统计时间（含）
        conn : sqlite3.Connection
            数据库连接对象
        secondary_trades : pandas.DataFrame
            二级交易记录
        primary_trades : pandas.DataFrame
            一级交易记录
        holded_bonds_info : pandas.DataFrame
            持有期间的债券基础信息
        insts_flow_all : pandas.DataFrame
            持有期间的债券的利息现金流
        value : pandas.DataFrame
            每日估值
        holded : pandas.DataFrame
            每日持仓
        capital : pandas.DataFrame
            持有期间的资本利得

    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        """
                构造函数.

                Parameters
                ----------
                    start_time : datetime.date
                        交易统计的开始时间
                    end_time : datetime.date
                        交易统计的截止时间（含）
        """

        self.start_time = start_time
        self.end_time = end_time
        self.conn = create_conn()

        self.secondary_trades = self._sum_secondary_trades()
        self.holded_bonds_info = self._holded_bonds_info()

        bond_type = pd.DataFrame({})
        if not self.holded_bonds_info.empty:
            bond_type = self.holded_bonds_info[[C.BOND_CODE, C.BOND_TYPE_NUM]]

        self.primary_trades = self._primary_trades()
        self.insts_flow_all = self._inst_cash_flow_all()
        self.value = self._daily_value_all()
        self.holded = self._daily_holded_all()
        self.capital = self._capital_gains_all()

        if not bond_type.empty:

            if not self.primary_trades.empty:
                self.primary_trades = self.primary_trades.reset_index(drop=False)
                self.primary_trades = pd.merge(self.primary_trades, bond_type, on=C.BOND_CODE, how='left')

            if not self.secondary_trades.empty:
                self.secondary_trades = pd.merge(self.secondary_trades, bond_type, on=C.BOND_CODE, how='left')

            if not self.insts_flow_all.empty:
                self.insts_flow_all = pd.merge(self.insts_flow_all, bond_type, on=C.BOND_CODE, how='left')

            if not self.value.empty:
                self.value = pd.merge(self.value, bond_type, on=C.BOND_CODE, how='left')

            if not self.holded.empty:
                self.holded = pd.merge(self.holded, bond_type, on=C.BOND_CODE, how='left')

            if not self.capital.empty:
                self.capital = pd.merge(self.capital, bond_type, on=C.BOND_CODE, how='left')

    def _get_raw_data(self, sql: str) -> pd.DataFrame:

        """
        从数据库获取原始数据.

        Args:
            sql (str): sql语句.

        Returns:
            pd.DataFrame: 数据库获取的交易数据.
        """

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        # 从数据库中获取数据
        raw = get_raw(self.conn, sql)

        return raw

    def _holded_bonds_info(self) -> pd.DataFrame:

        """
        交易期间持有的债券信息，不包括早期的收益凭证。
        Returns:
            pd.DataFrame: [C.BOND_NAME, C.BOND_FULL_NAME, C.BOND_CODE, C.BOND_TYPE_NUM, C.BOND_TYPE, C.ISSUE_DATE},
            C.MATURITY, C.COUPON_RATE_CURRENT, C.COUPON_RATE_ISSUE, C.ISSUE_AMT, C.ISSUE_PRICE, C.ISSUE_ORG,
            C.BOND_TERM, C.MARKET_CODE]

        """

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        sql = f"select distinct " \
              f"cc.{C.BOND_NAME}, " \
              f"bi.{C.BOND_FULL_NAME}, " \
              f"cc.{C.BOND_CODE}, " \
              f"bi.{C.BOND_TYPE_NUM}, " \
              f"bi.{C.BOND_TYPE}, " \
              f"bi.{C.ISSUE_DATE}, " \
              f"bi.{C.MATURITY}, " \
              f"bi.{C.COUPON_RATE_CURRENT}, " \
              f"bi.{C.COUPON_RATE_ISSUE}, " \
              f"bi.{C.ISSUE_AMT}, " \
              f"bi.{C.ISSUE_PRICE}, " \
              f"bi.{C.ISSUE_ORG}, " \
              f"bi.{C.BOND_TERM}, " \
              f"cc.{C.MARKET_CODE} " \
              f"from {C.COMP_DBNAME}.core_carrybondholds cc " \
              f"left join {C.COMP_DBNAME}.basic_bondbasicinfos bi " \
              f"on cc.{C.BOND_CODE} = bi.{C.BOND_CODE} " \
              f"where date(cc.{C.CARRY_DATE}) >= '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and date(cc.{C.CARRY_DATE}) <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' and cc.{C.CARRY_TYPE} = 3; "

        raw = self._get_raw_data(sql)

        if raw.empty:
            return pd.DataFrame({})

        # 如果当期利率为空，则取发行利率
        mask = pd.isna(raw.loc[:, C.COUPON_RATE_CURRENT])
        raw.loc[mask, C.COUPON_RATE_CURRENT] = raw.loc[mask, C.COUPON_RATE_ISSUE]

        # 由于早期购买的券商收益凭证不全，过滤掉不纳入统计
        mask = pd.isna(raw.loc[:, C.MARKET_CODE])

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw.loc[~mask, :])

        return raw.loc[~mask, :]

    # def get_holded_bonds_info(self) -> pd.DataFrame:
    #     return self.holded_bonds_info

    # def get_holded_bonds(self) -> pd.DataFrame:
    #     return self.holded

    #
    # def get_holding_bonds_endtime(self) -> pd.DataFrame:
    #     return self.holded[self.holded[C.DATE].dt.date == self.end_time]

    # def get_primary_trades(self) -> pd.DataFrame:
    #     return self.primary_trades

    # def get_secondary_trades(self) -> pd.DataFrame:
    #     return self.secondary_trades

    # def get_inst_cash_flow_all(self) -> pd.DataFrame:
    #     return self.insts_flow_all

    # def get_daily_value_all(self) -> pd.DataFrame:
    #     return self.value

    # def get_capital_all(self) -> pd.DataFrame:
    #     return self.capital

    # 1.1 全量利息现金流获取
    def _inst_cash_flow_all(self) -> pd.DataFrame:

        """
        统计区间内持仓债券的利息现金流

        Returns:
            pd.DataFrame: [C.BOND_CODE, C.BOND_NAME, C.INST_START_DATE, C.INST_END_DATE, C.ACCRUAL_DAYS, C.PERIOD_INST]

        """

        if self.start_time > self.end_time or self.holded_bonds_info.empty:
            return pd.DataFrame({})

        # 只取区间内持仓的债券利息现金流
        bonds_code_str = ', '.join([f"'{item}'" for item in (self.holded_bonds_info[C.BOND_CODE]).tolist()])

        sql = f"select " \
              f"bb.{C.BOND_CODE}, " \
              f"bb.{C.BOND_NAME}, " \
              f"bb.{C.INST_START_DATE}, " \
              f"bb.{C.INST_END_DATE}, " \
              f"bb.{C.ACCRUAL_DAYS}, " \
              f"bb.{C.PERIOD_INST} " \
              f"from {C.COMP_DBNAME}.basic_bondcashflows bb " \
              f"where {C.BOND_CODE} in (" + bonds_code_str + ") " + \
              f"and date(bb.{C.INST_END_DATE}) >= '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and date(bb.{C.INST_START_DATE}) <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' order by bb.{C.BOND_CODE};"

        raw = self._get_raw_data(sql)

        return raw

    # 1.2 单只债券利息现金流
    def get_inst_flow(self, bond_code: str) -> pd.DataFrame:

        """
        某支债券的利息现金流

        Parameters
        ----------
            bond_code : str
                债券代码

        Returns
        -------
            pd.DataFrame
                [C.DATE, C.INST_A_DAY]

        """

        if self.insts_flow_all.empty or (bond_code not in self.insts_flow_all[C.BOND_CODE].tolist()):
            return pd.DataFrame({})

        bond = self.insts_flow_all.loc[self.insts_flow_all[C.BOND_CODE] == bond_code]

        # 初始化
        inst_daily = pd.DataFrame(columns=[C.DATE, C.INST_A_DAY])

        # 取持仓时间段
        inst_daily[C.DATE] = self.holded.loc[self.holded[C.BOND_CODE] == bond_code, C.DATE]
        # 补充下缺失的日期
        inst_daily = inst_daily.set_index(C.DATE).resample('D').asfreq().reset_index()
        inst_daily[C.INST_A_DAY] = 0.0

        # Calculate the daily cash flow for each date
        for row in bond.index:
            date_range = pd.date_range(start=bond.loc[row][C.INST_START_DATE],
                                       end=bond.loc[row][C.INST_END_DATE] - datetime.timedelta(days=1),
                                       freq='D')
            inst_a_day = bond.loc[row][C.PERIOD_INST] / bond.loc[row][C.ACCRUAL_DAYS]

            # 由于计息天数等因素的差异，根据利息现金流分时间段赋值
            inst_daily.loc[inst_daily[C.DATE].isin(date_range), C.INST_A_DAY] = inst_a_day

        return inst_daily

    # 2.1 全量估值获取
    def _daily_value_all(self) -> pd.DataFrame:

        """
        查询全量每日估值，日期范围在两端各延长 60 天

        Returns
        -------
        pd.DataFrame
              [C.DEAL_DATE, C.DATE, C.BOND_CODE, C.BOND_NAME, C.VALUE_TYPE, C.VALUE_NET_PRICE]
        """

        if self.start_time > self.end_time or self.holded_bonds_info.empty:
            return pd.DataFrame({})

        # 由于数据库表对于非工作日没有估值，所以查询的时间区间前后各增加60个工作日，避免数据缺失
        bonds_code_str = ', '.join([f"'{item}'" for item in (self.holded_bonds_info[C.BOND_CODE]).tolist()])
        sql = f"select " \
              f"bv.{C.DEAL_DATE} as {C.DATE}, " \
              f"bv.{C.BOND_CODE}, " \
              f"bv.{C.BOND_NAME}, " \
              f"bv.{C.VALUE_TYPE}, " \
              f"bv.{C.VALUE_NET_PRICE} " \
              f"from {C.COMP_DBNAME}.basic_bondvaluations bv " \
              f"where {C.BOND_CODE} in (" + bonds_code_str + ") " + \
              f" and date(bv.{C.DEAL_DATE}) >= '" + \
              (self.start_time - datetime.timedelta(days=60)).strftime('%Y-%m-%d') + \
              f"' and date(bv.{C.DEAL_DATE}) <= '" + \
              (self.end_time + datetime.timedelta(days=60)).strftime('%Y-%m-%d') + \
              f"' order by bv.{C.BOND_CODE}, bv.{C.DEAL_DATE};"

        raw = self._get_raw_data(sql)

        return raw

    # 2.2 获取单支债券估值，注意源源数据库部分债券数据缺失不全
    def get_daily_value(self, bond_code: str) -> pd.DataFrame:

        """
        获取单支债券的每日估值

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.VALUE_NET_PRICE]
        """

        if (self.start_time > self.end_time or self.holded_bonds_info.empty or
                (bond_code not in self.holded_bonds_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        value_daily = pd.DataFrame(columns=[C.DATE])
        value_daily[C.DATE] = self.holded.loc[self.holded[C.BOND_CODE] == bond_code, C.DATE]

        # 如果数据库中没有估值，则默认为100
        if self.value.empty or (bond_code not in self.value[C.BOND_CODE].tolist()):
            value_daily[C.VALUE_NET_PRICE] = 100
            return value_daily

        bond = self.value.loc[self.value[C.BOND_CODE] == bond_code]
        bond = bond.drop_duplicates(C.DATE)

        # 非工作日数据缺失，取前一个工作日的估值
        # todo 如果中间有缺失，估值100会造成收益率曲线波动，取最后一个非空值是否更好
        bond = bond.set_index(C.DATE).resample('D').asfreq().reset_index()
        bond.ffill(inplace=True)

        value_daily = pd.merge(value_daily, bond[[C.DATE, C.VALUE_NET_PRICE]], on=C.DATE, how='left')

        # 如果数据库中没有估值，则默认为100；但如果中间有缺失，估值100会造成收益率曲线波动
        value_daily.fillna(100, inplace=True)

        return value_daily

    def _daily_holded_all(self) -> pd.DataFrame:

        """
        查询每日持仓数据，日期范围在两端各延长 60 天，不含委托投资

        Returns
        -------
        pd.DataFrame
              [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE]
        """

        if self.start_time > self.end_time or self.holded_bonds_info.empty:
            return pd.DataFrame({})

        # 注意：由于基础信息不全，这里排除了“委托投资”的持仓
        sql = f"select " \
              f"cc.{C.CARRY_DATE} as {C.DATE}, " \
              f"cc.{C.BOND_NAME}, " \
              f"cc.{C.BOND_CODE}, " \
              f"cc.{C.MARKET_CODE}, " \
              f"cc.{C.HOLD_AMT}, " \
              f"cc.{C.COST_FULL_PRICE}, " \
              f"cc.{C.COST_NET_PRICE} " \
              f"from {C.COMP_DBNAME}.core_carrybondholds cc " \
              f"where date(cc.{C.CARRY_DATE}) >= '" + \
              (self.start_time - datetime.timedelta(days=10)).strftime('%Y-%m-%d') + \
              f"' and date(cc.{C.CARRY_DATE}) <= '" + \
              (self.end_time + datetime.timedelta(days=10)).strftime('%Y-%m-%d') + \
              f"' and cc.{C.CARRY_TYPE} = 3 " \
              f"and cc.{C.PORTFOLIO_NO} not in ('Portfolio-20170919-008', 'Portfolio-20170713-023') " \
              f"order by cc.{C.CARRY_DATE};"

        raw = self._get_raw_data(sql)

        return raw

    def daily_holded_bond(_self, bond_code: str) -> pd.DataFrame:

        """
        按债券代码返回每日持仓

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE]
        """

        if (_self.start_time > _self.end_time or _self.holded_bonds_info.empty or
                (bond_code not in _self.holded_bonds_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        bond = _self.holded.loc[_self.holded[C.BOND_CODE] == bond_code]

        return bond

    def _primary_trades(self) -> pd.DataFrame:

        """
        查询一级交易数据（全市场）

        Returns
        -------
        pd.DataFrame
              [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.NET_PRICE, C.BOND_AMT_CASH]
        """

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        sql = f"select " \
              f"tc.{C.TRADE_DATE} as {C.DATE}, " \
              f"tc.{C.BOND_NAME}, " \
              f"tc.{C.BOND_CODE}, " \
              f"tc.{C.MARKET_CODE}, " \
              f"tc.{C.DIRECTION2} as {C.DIRECTION}, " \
              f"tc.{C.NET_PRICE2} as {C.NET_PRICE}, " \
              f"tc.{C.BOND_AMT_CASH2} as {C.BOND_AMT_CASH} " \
              f"from {C.COMP_DBNAME}.ext_requestdistributions tc " \
              f"where date(tc.{C.TRADE_DATE}) >= '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and date(tc.{C.TRADE_DATE}) <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.CHECK_STATUS} = 1 " \
              f"order by tc.{C.TRADE_DATE};"

        bonds = self._get_raw_data(sql)

        # 可能出现当天多笔分销认购，作汇总处理
        bonds_group = bonds.groupby([C.DATE, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.BOND_NAME]).agg({

            # 理论上中标的价格是一致的
            C.NET_PRICE: lambda x: x.iloc[0],
            C.BOND_AMT_CASH: lambda x: x.sum(),
        })

        return bonds_group

    def _bank_trades(_self) -> pd.DataFrame:

        """
        查询银行间市场的二级交易数据

        Returns
        -------
        pd.DataFrame
              [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.NET_PRICE, C.FULL_PRICE, C.BOND_AMT_CASH,
              C.ACCRUED_INST_CASH, C.TRADE_AMT, C.SETTLE_AMT]
        """

        if _self.start_time > _self.end_time:
            return pd.DataFrame({})

        sql = f"select " \
              f"tc.{C.SETTLEMENT_DATE} as {C.DATE}, " \
              f"tc.{C.BOND_NAME}, " \
              f"tc.{C.BOND_CODE}, " \
              f"tc.{C.MARKET_CODE}, " \
              f"tc.{C.DIRECTION}, " \
              f"tc.{C.NET_PRICE}, " \
              f"tc.{C.FULL_PRICE}, " \
              f"tc.{C.BOND_AMT_CASH}, " \
              f"tc.{C.ACCRUED_INST_CASH}, " \
              f"tc.{C.TRADE_AMT}, " \
              f"tc.{C.SETTLE_AMT} " \
              f"from {C.COMP_DBNAME}.trade_cashbonds tc " \
              f"where date(tc.{C.TRADE_TIME}) >= '" + \
              _self.start_time.strftime('%Y-%m-%d') + \
              f"' and date(tc.{C.TRADE_TIME}) <= '" + \
              _self.end_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.CHECK_STATUS} = 1 " \
              f"order by tc.{C.TRADE_TIME};"

        return _self._get_raw_data(sql)

    def _exchange_trades(self) -> pd.DataFrame:

        """
        查询交易所市场的二级交易数据

        Returns
        -------
        pd.DataFrame
              [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.NET_PRICE, C.FULL_PRICE, C.BOND_AMT_CASH,
              C.ACCRUED_INST_CASH, C.TRADE_AMT, C.SETTLE_AMT]
        """

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        sql = f"select " \
              f"tc.{C.TRADE_DATE} as {C.DATE}, " \
              f"tc.{C.BOND_NAME}, " \
              f"tc.{C.BOND_CODE}, " \
              f"tc.{C.MARKET_CODE}, " \
              f"tc.{C.DIRECTION}, " \
              f"tc.{C.NET_PRICE}, " \
              f"tc.{C.FULL_PRICE}, " \
              f"tc.{C.BOND_AMT_CASH2} as {C.BOND_AMT_CASH}, " \
              f"tc.{C.TRADE_AMT}, " \
              f"tc.{C.ACCRUED_INST_CASH2} as {C.ACCRUED_INST_CASH}, " \
              f"tc.{C.SETTLE_AMT} " \
              f"from {C.COMP_DBNAME}.trade_exchgcashbonds tc " \
              f"where date(tc.{C.TRADE_DATE}) >= '" + \
              self.start_time.strftime('%Y-%m-%d') + \
              f"' and date(tc.{C.TRADE_DATE}) <= '" + \
              self.end_time.strftime('%Y-%m-%d') + \
              f"' and tc.{C.CHECK_STATUS} = 1 " \
              f"order by tc.{C.TRADE_DATE};"

        return self._get_raw_data(sql)

    def _sum_secondary_trades(self) -> pd.DataFrame:
        """
        汇总银行间和交易所市场的二级交易市场数据

        Returns
        -------
        pd.DataFrame
              [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.NET_PRICE, C.FULL_PRICE, C.BOND_AMT_CASH,
              C.ACCRUED_INST_CASH, C.TRADE_AMT, C.SETTLE_AMT]
        """

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        bank = self._bank_trades()
        exchange = self._exchange_trades()

        if exchange.empty and bank.empty:
            return pd.DataFrame({})

        if exchange.empty:
            return bank

        if bank.empty:
            return exchange

        return pd.concat([bank, exchange], ignore_index=True)

    # 3.1 全量资本利得获取
    def _capital_gains_all(self) -> pd.DataFrame:
        """
        统计区间内的所有资本利得

        Returns
        -------
        pd.DataFrame
                [C.DATE, C.BOND_CODE, C.BOND_NAME, C.BOND_AMT_CASH, C.TRADE_AMT, C.MARKET_CODE, C.WEIGHT_NET_PRICE,
                C.COST_NET_PRICE, C.CAPITAL_GAINS]
        """

        if self.start_time > self.end_time or self.secondary_trades.empty:
            return pd.DataFrame({})

        # 只有卖出债券才有资本利得
        mask = (self.secondary_trades[C.DIRECTION] == 4)
        raw = self.secondary_trades.loc[mask, [C.DATE, C.BOND_CODE, C.BOND_NAME, C.BOND_AMT_CASH, C.TRADE_AMT]]

        if raw.empty:
            return pd.DataFrame({})

        raw_group = raw.groupby([C.DATE, C.BOND_CODE, C.BOND_NAME]).agg({
            C.BOND_AMT_CASH: lambda x: x.sum(),
            C.TRADE_AMT: lambda x: x.sum(),
        })

        # 当日的交易加权净价
        raw_group[C.WEIGHT_NET_PRICE] = raw_group[C.TRADE_AMT] / raw_group[C.BOND_AMT_CASH] * 100

        # Create a copy of self.holded to avoid modifying the original DataFrame
        holded_copy = self.holded.copy()

        # 3.2 从C.DATE列加一天，获取前一天的成本净价
        # add one day from the C.DATE column，get previous day's net cost price
        holded_copy[C.DATE] = holded_copy[C.DATE] + pd.Timedelta(days=1)

        # Merge raw_group with the modified holded_copy
        raw_group = pd.merge(raw_group,
                             holded_copy[[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME, C.COST_NET_PRICE]],
                             on=[C.DATE, C.BOND_CODE, C.BOND_NAME], how='left')

        # 3.3 理论上前一天的成本净价没有空值，但是源数据库数据有问题(20161219,160010)，暂时做此处理
        raw_group[C.COST_NET_PRICE] = raw_group[C.COST_NET_PRICE].fillna(100)
        raw_group[C.CAPITAL_GAINS] = ((raw_group[C.WEIGHT_NET_PRICE] - raw_group[C.COST_NET_PRICE])
                                      * raw_group[C.BOND_AMT_CASH] / 100)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw_group)

        return raw_group

    # 4.1 计算单只债券的利息
    def get_daily_insts(_self, bond_code: str) -> pd.DataFrame:

        """
        单支债券的每日利息

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_NAME, C.BOND_KEY, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, COST_NET_PRICE,
            C.BOND_TYPE, C.INST_A_DAY]
        """

        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        inst = _self.get_inst_flow(bond_code)

        # 按照数据库设计的逻辑，当到期日的第二天为非工作日时，无利息流，但是仍然有持仓和资金占用
        if inst.empty:
            inst = pd.DataFrame(columns=[C.DATE, C.INST_A_DAY])
            inst[C.DATE] = raw[C.DATE]
            inst[C.INST_A_DAY] = 0.0

        raw_inst = pd.merge(raw, inst, on=C.DATE, how='left')
        raw_inst[C.INST_A_DAY] = (raw_inst[C.INST_A_DAY] * raw_inst[C.HOLD_AMT] / 100)
        raw_inst.fillna(0, inplace=True)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw_inst)

        return raw_inst

    # 4.2 计算单只债券的资本利得
    def get_capital_gains(self, bond_code: str) -> pd.DataFrame:

        """
        单支债券的资本利得

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_CODE, C.BOND_NAME, C.BOND_AMT_CASH, C.TRADE_AMT, C.MARKET_CODE, C.WEIGHT_NET_PRICE,
            C.COST_NET_PRICE, C.CAPITAL_GAINS]
        """

        if self.start_time > self.end_time or self.capital.empty or bond_code not in self.capital[C.BOND_CODE].tolist():
            return pd.DataFrame({})

        mask = (self.capital[C.BOND_CODE] == bond_code)
        capital = self.capital.loc[mask, :]

        return capital

    # 4.3 计算单只债券的净价浮盈
    def get_net_profit(_self, bond_code: str) -> pd.DataFrame:

        """
        单支债券的净价浮盈

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE,
            C.VALUE_NET_PRICE, C.NET_PROFIT]
        """
        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        value = _self.get_daily_value(bond_code)

        raw_value = pd.merge(raw, value, on=C.DATE, how='left')
        raw_value[C.NET_PROFIT] = (raw_value[C.HOLD_AMT] / 100 *
                                   (raw_value[C.VALUE_NET_PRICE] - raw_value[C.COST_NET_PRICE])).fillna(0)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw_value)

        return raw_value

    # 4.4 计算单只债券的总收益
    def sum_profits(self, bond_code: str) -> pd.DataFrame:
        """
        汇总利息收入、资本利得和净价浮盈，计算总收益

        Parameters
        ----------
        bond_code : str
            债券代码

        Returns
        -------
        pd.DataFrame
            [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE,
            C.BOND_TYPE, C.CAPITAL_GAINS, C.INST_A_DAY,C.VALUE_NET_PRICE, C.NET_PROFIT, C.TOTAL_PROFIT,C.CAPITAL_OCCUPY]
        """

        if (self.start_time > self.end_time or self.holded_bonds_info.empty or
                bond_code not in self.holded_bonds_info[C.BOND_CODE].tolist()):
            return pd.DataFrame({})

        # 如果有该债券的持仓，这两项一定不会是空值
        daily_insts = self.get_daily_insts(bond_code)
        net_profit = self.get_net_profit(bond_code)

        bond = self.daily_holded_bond(bond_code).copy()

        capital = self.get_capital_gains(bond_code)

        # merge capital gains first
        if capital.empty:
            bond[C.CAPITAL_GAINS] = 0.0
        else:
            # 如果当日卖空,则持仓为0
            bond = pd.merge(bond, capital[[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME, C.CAPITAL_GAINS]],
                            on=[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME], how='outer')
            bond[C.CAPITAL_GAINS] = bond[C.CAPITAL_GAINS].fillna(0)

        bond = pd.merge(bond, daily_insts[[C.DATE, C.INST_A_DAY]], on=C.DATE, how='left')
        bond = pd.merge(bond, net_profit[[C.DATE, C.VALUE_NET_PRICE, C.NET_PROFIT]], on=C.DATE, how='left')
        bond[C.MARKET_CODE] = bond[C.MARKET_CODE].ffill()

        # 找出包含缺失值的列
        columns_with_none = bond.columns[bond.isna().any()]

        # 对这些列中的缺失值赋值为 0
        bond[columns_with_none] = bond[columns_with_none].astype(float).fillna(0)
        # 计算总收益
        bond[C.TOTAL_PROFIT] = bond[C.CAPITAL_GAINS] + bond[C.INST_A_DAY] + bond[C.NET_PROFIT]
        # 4.4.1 资金占用
        bond[C.CAPITAL_OCCUPY] = bond[C.HOLD_AMT] * bond[C.COST_FULL_PRICE] / 100

        mask = (bond[C.DATE] >= pd.to_datetime(self.start_time)) & (bond[C.DATE] <= pd.to_datetime(self.end_time))

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(bond)

        return bond.loc[mask, :]

    def get_all_profit_data(self):
        """
        汇总所有债券的总收益
        :return:
            [C.DATE, C.BOND_NAME, C.BOND_CODE, C.MARKET_CODE, C.HOLD_AMT, C.COST_FULL_PRICE, C.COST_NET_PRICE,
            C.BOND_TYPE, C.CAPITAL_GAINS, C.INST_A_DAY,C.VALUE_NET_PRICE, C.NET_PROFIT, C.TOTAL_PROFIT,C.CAPITAL_OCCUPY
            C.ISSUE_ORG]
        """

        # bonds_info = self.get_holded_bonds_info()
        bonds_info = self.holded_bonds_info

        # print(bonds_info)

        if bonds_info.empty:
            return pd.DataFrame({})
        bond_codes = bonds_info[C.BOND_CODE].tolist()
        bond_all = pd.DataFrame({})

        # 生成一个包含所有债券收益情况的DataFrame
        for bond_code in bond_codes:
            bond_all = pd.concat([bond_all, self.sum_profits(bond_code)], ignore_index=True)

        # 补充债券代码和发行机构
        bond_all = pd.merge(bond_all, bonds_info[[C.BOND_CODE, C.ISSUE_ORG]], on=C.BOND_CODE, how='left')

        return bond_all


class CDTx(SecurityTx):
    """
    存单交易类
    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        super().__init__(start_time, end_time)

        if not self.primary_trades.empty:
            self.primary_trades = self.primary_trades.loc[self.primary_trades[C.BOND_TYPE_NUM] == 26, :]
        if not self.secondary_trades.empty:
            self.secondary_trades = self.secondary_trades.loc[self.secondary_trades[C.BOND_TYPE_NUM] == 26, :]
        if not self.insts_flow_all.empty:
            self.insts_flow_all = self.insts_flow_all.loc[self.insts_flow_all[C.BOND_TYPE_NUM] == 26, :]
        if not self.value.empty:
            self.value = self.value.loc[self.value[C.BOND_TYPE_NUM] == 26, :]
        if not self.holded.empty:
            self.holded = self.holded.loc[self.holded[C.BOND_TYPE_NUM] == 26, :]
        if not self.capital.empty:
            self.capital = self.capital.loc[self.capital[C.BOND_TYPE_NUM] == 26, :]

        if not self.holded_bonds_info.empty:
            self.holded_bonds_info = self.holded_bonds_info.loc[self.holded_bonds_info[C.BOND_TYPE_NUM] == 26, :]


class BondTx(SecurityTx):
    """
    债券交易类
    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        super().__init__(start_time, end_time)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(self.holded_bonds_info[[C.BOND_TYPE_NUM, C.BOND_NAME]])

        if not self.primary_trades.empty:
            self.primary_trades = self.primary_trades.loc[self.primary_trades[C.BOND_TYPE_NUM] != 26, :]
        if not self.secondary_trades.empty:
            self.secondary_trades = self.secondary_trades.loc[self.secondary_trades[C.BOND_TYPE_NUM] != 26, :]
        if not self.insts_flow_all.empty:
            self.insts_flow_all = self.insts_flow_all.loc[self.insts_flow_all[C.BOND_TYPE_NUM] != 26, :]
        if not self.value.empty:
            self.value = self.value.loc[self.value[C.BOND_TYPE_NUM] != 26, :]
        if not self.holded.empty:
            self.holded = self.holded.loc[self.holded[C.BOND_TYPE_NUM] != 26, :]
        if not self.capital.empty:
            self.capital = self.capital.loc[self.capital[C.BOND_TYPE_NUM] != 26, :]
        if not self.holded_bonds_info.empty:
            self.holded_bonds_info = self.holded_bonds_info.loc[self.holded_bonds_info[C.BOND_TYPE_NUM] != 26, :]
