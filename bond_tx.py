# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond_tx
# Description: This module contains classes for handling security transactions, specifically for bonds and CDs.
import datetime
import pandas as pd
from numpy import float64

from utils.db_util import get_raw, create_conn
from utils.db_util import Constants as C


# The SecurityTx class represents a security transaction.
class SecurityTx:
    """
        A class used to represent a Security Transaction.

        ...

        Attributes
        ----------
        start_time : datetime.date
            The start date of the transaction
        end_time : datetime.date
            The end date of the transaction
        conn : sqlite3.Connection
            The connection to the database
        trades : pandas.DataFrame
            The trades made during the transaction
        holded_info : pandas.DataFrame
            Information about the bonds held during the transaction
        request : pandas.DataFrame
            The request distributions of the transaction
        insts_flow : pandas.DataFrame
            The cash flow of the institutions involved in the transaction
        value : pandas.DataFrame
            The daily value of all the bonds involved in the transaction
        holded : pandas.DataFrame
            The daily holded bonds of all the bonds involved in the transaction
        capital : pandas.DataFrame
            The capital of all the bonds involved in the transaction

        Methods
        -------
        _get_raw_data(sql: str) -> pd.DataFrame:
            Retrieves raw data from the database using the provided SQL query.
        get_holded_bonds_info() -> pd.DataFrame:
            Returns information about the bonds held during the transaction.
        get_holded_bonds() -> pd.DataFrame:
            Returns the daily holded bonds of all the bonds involved in the transaction.
        get_request_distributions() -> pd.DataFrame:
            Returns the request distributions of the transaction.
        get_all_trades() -> pd.DataFrame:
            Returns the trades made during the transaction.
        get_inst_cash_flow_all() -> pd.DataFrame:
            Returns the cash flow of the institutions involved in the transaction.
        get_daily_value_all() -> pd.DataFrame:
            Returns the daily value of all the bonds involved in the transaction.
        get_capital_all() -> pd.DataFrame:
            Returns the capital of all the bonds involved in the transaction.
        _inst_cash_flow_all() -> pd.DataFrame:
            Retrieves the cash flow of all institutions involved in the transaction from the database.
        get_inst_flow(bond_code: str) -> pd.DataFrame:
            Returns the cash flow of a specific institution involved in the transaction.
        _daily_value_all() -> pd.DataFrame:
            Retrieves the daily value of all bonds involved in the transaction from the database.
        get_daily_value(bond_code: str) -> pd.DataFrame:
            Returns the daily value of a specific bond involved in the transaction.
        _daily_holded_all() -> pd.DataFrame:
            Retrieves the daily holded bonds of all bonds involved in the transaction from the database.
        daily_holded_bond(_self, bond_code: str) -> pd.DataFrame:
            Returns the daily holded bonds of a specific bond involved in the transaction.
        _request_distributions() -> pd.DataFrame:
            Retrieves the request distributions of the transaction from the database.
        _bank_trades(_self) -> pd.DataFrame:
            Retrieves the trades made by banks during the transaction from the database.
        _exchange_trades(self) -> pd.DataFrame:
            Retrieves the trades made on the exchange during the transaction from the database.
        _sum_all_trades(self) -> pd.DataFrame:
            Returns the sum of all trades made during the transaction.
        _capital_all(self) -> pd.DataFrame:
            Retrieves the capital of all bonds involved in the transaction from the database.
        get_capital(self, bond_code: str) -> pd.DataFrame:
            Returns the capital of a specific bond involved in the transaction.
        get_daily_insts(_self, bond_code: str) -> pd.DataFrame:
            Returns the daily institutions of a specific bond involved in the transaction.
        get_net_profit(_self, bond_code: str) -> pd.DataFrame:
            Returns the net profit of a specific bond involved in the transaction.
        _holded_bonds_info(self) -> pd.DataFrame:
            Retrieves information about the bonds held during the transaction from the database.
        sum_all_profits(self, bond_code: str) -> pd.DataFrame:
            Returns the sum of all profits made from a specific bond during the transaction.
    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        """
                Constructs all the necessary attributes for the SecurityTx object.

                Parameters
                ----------
                    start_time : datetime.date
                        The start date of the transaction
                    end_time : datetime.date
                        The end date of the transaction
        """

        self.start_time = start_time
        self.end_time = end_time
        self.conn = create_conn()

        self.trades = self._sum_all_trades()
        self.holded_info = self._holded_bonds_info()

        bond_type = pd.DataFrame({})
        if not self.holded_info.empty:
            bond_type = self.holded_info[[C.BOND_CODE, C.BOND_TYPE_NUM]]

        self.request = self._request_distributions()
        self.insts_flow = self._inst_cash_flow_all()
        self.value = self._daily_value_all()
        self.holded = self._daily_holded_all()
        self.capital = self._capital_gains_all()

        if not bond_type.empty:

            if not self.request.empty:
                self.request = self.request.reset_index(drop=False)
                self.request = pd.merge(self.request, bond_type, on=C.BOND_CODE, how='left')

            if not self.trades.empty:
                self.trades = pd.merge(self.trades, bond_type, on=C.BOND_CODE, how='left')

            if not self.insts_flow.empty:
                self.insts_flow = pd.merge(self.insts_flow, bond_type, on=C.BOND_CODE, how='left')

            if not self.value.empty:
                self.value = pd.merge(self.value, bond_type, on=C.BOND_CODE, how='left')

            if not self.holded.empty:
                self.holded = pd.merge(self.holded, bond_type, on=C.BOND_CODE, how='left')

            if not self.capital.empty:
                self.capital = pd.merge(self.capital, bond_type, on=C.BOND_CODE, how='left')

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        if self.start_time > self.end_time:
            return pd.DataFrame({})

        # 从数据库中获取数据
        raw = get_raw(self.conn, sql)

        return raw

    def _holded_bonds_info(self) -> pd.DataFrame:

        """
        Retrieves information about the bonds held during the transaction from the database.

        This method constructs a SQL query to fetch the held bonds data from the database.
        The query selects distinct bond name, bond full name, bond code, bond type number, bond type,
        issue date, maturity, current coupon rate, issue coupon rate, issue amount, issue price, issue organization,
        bond term, and market code from the core_carrybondholds and basic_bondbasicinfos tables in the database.
        The query filters the data based on the carry date and carry type.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing information about the bonds held during the transaction.
            If the start time is later than the end time, an empty DataFrame is returned.
            If the current coupon rate is not available, the issue coupon rate is used.
            If the market code is not available, the bond is excluded from the DataFrame.
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
        return raw.loc[~mask, :]

    def get_holded_bonds_info(self) -> pd.DataFrame:
        return self.holded_info

    def get_holded_bonds(self) -> pd.DataFrame:
        return self.holded

    def get_holding_bonds_endtime(self) -> pd.DataFrame:
        return self.holded[self.holded[C.DATE].dt.date == self.end_time]

    def get_primary_trades(self) -> pd.DataFrame:
        return self.request

    def get_secondary_trades(self) -> pd.DataFrame:
        return self.trades

    def get_inst_cash_flow_all(self) -> pd.DataFrame:
        return self.insts_flow

    def get_daily_value_all(self) -> pd.DataFrame:
        return self.value

    def get_capital_all(self) -> pd.DataFrame:
        return self.capital

    # 1.1 全量利息现金流获取
    def _inst_cash_flow_all(self) -> pd.DataFrame:

        """
        Retrieves the cash flow of all institutions involved in the transaction from the database.

        This method constructs a SQL query to fetch the cash flow data from the database.
        The query selects the bond code, bond name, start date, end date, accrual days, and period inst
        from the basic_bondcashflows table in the database.
        The query filters the data based on the bond code and the date range.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the cash flow of all institutions involved in the transaction.
            If the start time is later than the end time or if there is no held bond information,
            an empty DataFrame is returned.
        """

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

        # 只取区间内持仓的债券利息现金流
        bonds_code_str = ', '.join([f"'{item}'" for item in (self.holded_info[C.BOND_CODE]).tolist()])

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
            Retrieves the cash flow of a specific institution involved in the transaction.

            This method filters the cash flow data based on the provided bond code. It then constructs a DataFrame that
            represents the daily cash flow of the institution. The method fills in missing dates in the cash flow data
            and calculates the daily cash flow based on the period inst and accrual days.

            Parameters
            ----------
            bond_code : str
                The bond code of the institution whose cash flow is to be retrieved.

            Returns
            -------
            pd.DataFrame
                A DataFrame containing the daily cash flow of the institution. If the bond code is not found in the
                cash flow data or if the cash flow data is empty, an empty DataFrame is returned.
        """

        if self.insts_flow.empty or (bond_code not in self.insts_flow[C.BOND_CODE].tolist()):
            return pd.DataFrame({})

        # Filter the cash flow data based on the bond code
        bond = self.insts_flow.loc[self.insts_flow[C.BOND_CODE] == bond_code]

        # Initialize a DataFrame to store the daily cash flow of the institution
        inst_daily = pd.DataFrame(columns=[C.DATE, C.INST_A_DAY])

        # 取持仓时间段
        inst_daily[C.DATE] = self.holded.loc[self.holded[C.BOND_CODE] == bond_code][C.DATE].copy()
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

        # 将inst_daily[C.INST_A_DAY]中的缺失值填充为0
        # inst_daily[C.INST_A_DAY] = inst_daily[C.INST_A_DAY].fillna(0.0).astype(float64)
        # 查看inst_daily[C.INST_A_DAY]存储的值类型
        # print(inst_daily[C.INST_A_DAY].dtype)
        return inst_daily

    # 2.1 全量估值获取
    def _daily_value_all(self) -> pd.DataFrame:

        """
        Retrieves the daily value of all bonds involved in the transaction from the database.

        This method constructs a SQL query to fetch the daily value data from the database.
        The query selects the deal date, bond code, bond name, value type, and net price
        from the basic_bondvaluations table in the database.
        The query filters the data based on the bond code and the date range.
        The date range is extended by 60 days on both ends to account for non-working days.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the daily value of all bonds involved in the transaction.
            If the start time is later than the end time or if there is no held bond information,
            an empty DataFrame is returned.
        """

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

        # 由于数据库表对于非工作日没有估值，所以查询的时间区间前后各增加60个工作日，避免数据缺失
        bonds_code_str = ', '.join([f"'{item}'" for item in (self.holded_info[C.BOND_CODE]).tolist()])
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
        Retrieves the daily value of a specific bond involved in the transaction.

        This method filters the daily value data based on the provided bond code. It then constructs a DataFrame that
        represents the daily value of the bond. The method fills in missing dates in the value data and assigns a
        default value of 100 to dates for which the value data is not available in the database.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose daily value is to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the daily value of the bond. If the bond code is not found in the
            value data or if the value data is empty, a DataFrame with a default value of 100 is returned.
        """

        if (self.start_time > self.end_time or self.holded_info.empty or
                (bond_code not in self.holded_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        value_daily = pd.DataFrame(columns=[C.DATE])
        value_daily[C.DATE] = self.holded.loc[self.holded[C.BOND_CODE] == bond_code][C.DATE]

        # 如果数据库中没有估值，则默认为100
        if self.value.empty or (bond_code not in self.value[C.BOND_CODE].tolist()):
            value_daily[C.VALUE_NET_PRICE] = 100
            return value_daily

        bond = self.value.loc[self.value[C.BOND_CODE] == bond_code]
        bond = bond.drop_duplicates(C.DATE)

        # 非工作日数据缺失，取前一个工作日的估值
        bond = bond.set_index(C.DATE).resample('D').asfreq().reset_index()
        bond.ffill(inplace=True)

        value_daily = pd.merge(value_daily, bond[[C.DATE, C.VALUE_NET_PRICE]], on=C.DATE, how='left')

        # 如果数据库中没有估值，则默认为100；但如果中间有缺失，估值100会造成收益率曲线波动
        value_daily.fillna(100, inplace=True)

        return value_daily

    def _daily_holded_all(self) -> pd.DataFrame:

        """
        Retrieves the daily held bonds of all bonds involved in the transaction from the database.

        This method constructs a SQL query to fetch the daily held bonds data from the database.
        The query selects the carry date, bond name, bond code, market code, hold amount,
        cost full price, and cost net price from the core_carrybondholds table in the database.
        The query filters the data based on the carry date and excludes certain portfolio numbers.
        The date range is extended by 10 days on both ends to account for non-working days.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the daily held bonds of all bonds involved in the transaction.
            If the start time is later than the end time or if there is no held bond information,
            an empty DataFrame is returned.
        """

        if self.start_time > self.end_time or self.holded_info.empty:
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
        Retrieves the daily held bonds of a specific bond involved in the transaction.

        This method filters the daily held bonds data based on the provided bond code.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose daily held bonds are to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the daily held bonds of the bond. If the bond code is not found in the
            held bonds data or if the held bonds data is empty, an empty DataFrame is returned.
        """

        if (_self.start_time > _self.end_time or _self.holded_info.empty or
                (bond_code not in _self.holded_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        bond = _self.holded.loc[_self.holded[C.BOND_CODE] == bond_code]

        return bond

    def _request_distributions(self) -> pd.DataFrame:

        """
        Retrieves the request distributions of the transaction from the database.

        This method constructs a SQL query to fetch the request distributions data from the database.
        The query selects the trade date, bond name, bond code, market code, direction, net price, and bond amount in
        cash from the ext_requestdistributions table in the database.
        The query filters the data based on the trade date and checks the status of the request.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the request distributions of the transaction grouped by date, bond code, market code,
            direction, and bond name. The DataFrame aggregates the net price and bond amount in cash.
            If the start time is later than the end time, an empty DataFrame is returned.
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
        Retrieves the transactions in the interbank market during the transaction from the database.

        This method constructs a SQL query to fetch the bank trades data from the database.
        The query selects the settlement date, bond name, bond code, market code, direction, net price, full price,
        bond amount in cash, accrued inst cash, trade amount, and settle amount
        from the trade_cashbonds table in the database.
        The query filters the data based on the trade time and checks the status of the trade.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the trades made by banks during the transaction.
            If the start time is later than the end time, an empty DataFrame is returned.
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
        Retrieves the transactions on the exchange during the transaction from the database.

        This method constructs a SQL query to fetch the exchange trades data from the database.
        The query selects the trade date, bond name, bond code, market code, direction, net price, full price,
        bond amount in cash, trade amount, accrued inst cash, and settle amount
        from the trade_exchgcashbonds table in the database.
        The query filters the data based on the trade date and checks the status of the trade.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the trades made on the exchange during the transaction.
            If the start time is later than the end time, an empty DataFrame is returned.
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

    def _sum_all_trades(self) -> pd.DataFrame:
        """
        Retrieves all trades made during the transaction from both the interbank market and the exchange.

        This method calls the _bank_trades and _exchange_trades methods to fetch the trades data from the database.
        The data from both sources is then concatenated into a single DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing all trades made during the transaction.
            If the start time is later than the end time, an empty DataFrame is returned.
            If there are no trades on the exchange, only the bank trades are returned.
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
        Retrieves the capital of all bonds involved in the transaction from the database.

        This method constructs a DataFrame that represents the capital of all bonds involved in the transaction.
        The DataFrame is constructed by grouping the trades data based on the date, bond code, and bond name.
        The method calculates the weighted net price for each group and merges the result with the held bonds data.
        The method then calculates the capital gains for each group.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the capital of all bonds involved in the transaction.
            If the start time is later than the end time or if there are no trades, an empty DataFrame is returned.
            If there are no trades for a specific bond, the capital gains for that bond are set to 0.
        """

        if self.start_time > self.end_time or self.trades.empty:
            return pd.DataFrame({})

        # 只有卖出债券才有资本利得
        mask = (self.trades[C.DIRECTION] == 4)
        raw = self.trades.loc[mask, [C.DATE, C.BOND_CODE, C.BOND_NAME, C.BOND_AMT_CASH, C.TRADE_AMT]]

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

        # 3.2 从C.DATE列加一天，获取前一天的净成本价
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

        return raw_group

    # 4.1 计算单只债券的利息
    def get_daily_insts(_self, bond_code: str) -> pd.DataFrame:

        """
        Retrieves the daily institutions of a specific bond involved in the transaction.

        This method first retrieves the daily held bonds of the bond using the provided bond code.
        If there are no daily held bonds, an empty DataFrame is returned.
        The method then retrieves the cash flow of the institution involved in the transaction.
        The daily institutions are calculated by merging the daily held bonds and the cash flow data.
        The daily institutions are calculated as the product of the daily cash flow and the daily held bonds.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose daily institutions are to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the daily institutions of the bond.
            If there are no daily held bonds or if the bond code is not found in the daily held bonds data,
            an empty DataFrame is returned.
        """

        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        inst = _self.get_inst_flow(bond_code)
        # if inst.empty:
        #     print(bond_code)
        #     print(raw)

        # 按照数据库设计的逻辑，当到期日的第二天为非工作日时，无利息流，但是仍然有持仓和资金占用
        if inst.empty:
            inst = pd.DataFrame(columns=[C.DATE, C.INST_A_DAY])
            inst[C.DATE] = raw[C.DATE]
            inst[C.INST_A_DAY] = 0.0

        raw_inst = pd.merge(raw, inst, on=C.DATE, how='left')
        raw_inst[C.INST_A_DAY] = (raw_inst[C.INST_A_DAY] * raw_inst[C.HOLD_AMT] / 100)
        raw_inst.fillna(0, inplace=True)

        return raw_inst

    # 4.2 计算单只债券的资本利得
    def get_capital_gains(self, bond_code: str) -> pd.DataFrame:

        """
        Retrieves the capital gains of a specific bond involved in the transaction.

        This method filters the capital data based on the provided bond code.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose capital is to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the capital of the bond. If the start time is later than the end time,
            if the capital data is empty, or if the bond code is not found in the capital data,
            an empty DataFrame is returned.
        """

        if self.start_time > self.end_time or self.capital.empty or bond_code not in self.capital[C.BOND_CODE].tolist():
            return pd.DataFrame({})

        mask = (self.capital[C.BOND_CODE] == bond_code)
        capital = self.capital.loc[mask, :]

        return capital

    # 4.3 计算单只债券的净价浮盈
    def get_net_profit(_self, bond_code: str) -> pd.DataFrame:

        """
        Retrieves the net profit of a specific bond involved in the transaction.

        This method first retrieves the daily held bonds of the bond using the provided bond code.
        If there are no daily held bonds, an empty DataFrame is returned.
        The method then retrieves the daily value of the bond.
        The net profit is calculated by merging the daily held bonds and the daily value data.
        The net profit is calculated as the product of the daily held bonds and the difference between
        the daily value and the cost net price.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose net profit is to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the net profit of the bond.
            If there are no daily held bonds or if the bond code is not found in the daily held bonds data,
            an empty DataFrame is returned.
        """
        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        value = _self.get_daily_value(bond_code)

        raw_value = pd.merge(raw, value, on=C.DATE, how='left')
        raw_value[C.NET_PROFIT] = (raw_value[C.HOLD_AMT] / 100 *
                                   (raw_value[C.VALUE_NET_PRICE] - raw_value[C.COST_NET_PRICE])).fillna(0)

        return raw_value

    # 4.4 计算单只债券的总收益
    def sum_profits(self, bond_code: str) -> pd.DataFrame:
        """
        Calculates the total profits for a specific bond involved in the transaction.

        This method first checks if the bond is held during the transaction period.
        If not, an empty DataFrame is returned.
        The method then retrieves the daily institutions and net profit of the bond.
        It also retrieves the daily held bonds and capital of the bond.
        The method then calculates the capital gains, merges the data, and fills in missing values.
        Finally, it calculates the total profits and capital occupation.

        Parameters
        ----------
        bond_code : str
            The bond code of the bond whose total profits are to be calculated.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the total profits of the bond.
            If the bond is not held during the transaction period, an empty DataFrame is returned.
        """

        if (self.start_time > self.end_time or self.holded_info.empty or
                bond_code not in self.holded_info[C.BOND_CODE].tolist()):
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

        # merge daily institutions and net profit
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
        return bond.loc[mask, :]

    def get_all_profit_data(self):

        bonds_info = self.get_holded_bonds_info()

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

    def get_stime(self) -> datetime.date:
        return self.start_time

    def get_etime(self) -> datetime.date:
        return self.end_time


class CDTx(SecurityTx):
    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        super().__init__(start_time, end_time)

        if not self.request.empty:
            self.request = self.request.loc[self.request[C.BOND_TYPE_NUM] == 26, :]
        if not self.trades.empty:
            self.trades = self.trades.loc[self.trades[C.BOND_TYPE_NUM] == 26, :]
        if not self.insts_flow.empty:
            self.insts_flow = self.insts_flow.loc[self.insts_flow[C.BOND_TYPE_NUM] == 26, :]
        if not self.value.empty:
            self.value = self.value.loc[self.value[C.BOND_TYPE_NUM] == 26, :]
        if not self.holded.empty:
            self.holded = self.holded.loc[self.holded[C.BOND_TYPE_NUM] == 26, :]
        if not self.capital.empty:
            self.capital = self.capital.loc[self.capital[C.BOND_TYPE_NUM] == 26, :]

        if not self.holded_info.empty:
            self.holded_info = self.holded_info.loc[self.holded_info[C.BOND_TYPE_NUM] == 26, :]


class BondTx(SecurityTx):
    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        super().__init__(start_time, end_time)

        if not self.request.empty:
            self.request = self.request.loc[self.request[C.BOND_TYPE_NUM] != 26, :]
        if not self.trades.empty:
            self.trades = self.trades.loc[self.trades[C.BOND_TYPE_NUM] != 26, :]
        if not self.insts_flow.empty:
            self.insts_flow = self.insts_flow.loc[self.insts_flow[C.BOND_TYPE_NUM] != 26, :]
        if not self.value.empty:
            self.value = self.value.loc[self.value[C.BOND_TYPE_NUM] != 26, :]
        if not self.holded.empty:
            self.holded = self.holded.loc[self.holded[C.BOND_TYPE_NUM] != 26, :]
        if not self.capital.empty:
            self.capital = self.capital.loc[self.capital[C.BOND_TYPE_NUM] != 26, :]
        if not self.holded_info.empty:
            self.holded_info = self.holded_info.loc[self.holded_info[C.BOND_TYPE_NUM] != 26, :]
