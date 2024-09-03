# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond_tx
# Description: simple introduction of the code
import datetime

import pandas as pd

from utils.db_util import get_raw, create_conn
from utils.db_util import Constants as C


class SecurityTx:
    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
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
        self.capital = self._capital_all()

        if not bond_type.empty:

            if not self.request.empty:
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

    def get_holded_bonds_info(self) -> pd.DataFrame:
        return self.holded_info

    def get_holded_bonds(self) -> pd.DataFrame:
        return self.holded

    def get_request_distributions(self) -> pd.DataFrame:
        return self.request

    def get_all_trades(self) -> pd.DataFrame:
        return self.trades

    def get_inst_cash_flow_all(self) -> pd.DataFrame:
        return self.insts_flow

    def get_daily_value_all(self) -> pd.DataFrame:
        return self.value

    def get_capital_all(self) -> pd.DataFrame:
        return self.capital

    def _inst_cash_flow_all(self) -> pd.DataFrame:

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

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

    def get_inst_flow(self, bond_code: str) -> pd.DataFrame:

        if self.insts_flow.empty or (bond_code not in self.insts_flow[C.BOND_CODE].tolist()):
            return pd.DataFrame({})

        bond = self.insts_flow.loc[self.insts_flow[C.BOND_CODE] == bond_code]

        inst_daily = pd.DataFrame(columns=[C.DATE, C.INST_A_DAY])

        # 取持仓时间段
        inst_daily[C.DATE] = self.holded.loc[self.holded[C.BOND_CODE] == bond_code][C.DATE].copy()
        # 补充下缺失的日期
        inst_daily = inst_daily.set_index(C.DATE).resample('D').asfreq().reset_index()

        for row in bond.index:
            date_range = pd.date_range(start=bond.loc[row][C.INST_START_DATE],
                                       end=bond.loc[row][C.INST_END_DATE] - datetime.timedelta(days=1),
                                       freq='D')
            inst_a_day = bond.loc[row][C.PERIOD_INST] / bond.loc[row][C.ACCRUAL_DAYS]

            # 由于计息天数等因素的差异，根据利息现金流分时间段赋值
            inst_daily.loc[inst_daily[C.DATE].isin(date_range), C.INST_A_DAY] = inst_a_day

        return inst_daily

    def _daily_value_all(self) -> pd.DataFrame:

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

        # 由于数据库表对于非工作日没有估值，所以查询的时间区间前后各增加15个工作日，避免数据缺失
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

        # if raw.empty:
        #     return pd.DataFrame({})

        return raw

    # todo 有bug
    def get_daily_value(self, bond_code: str) -> pd.DataFrame:

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
        # bond.drop_duplicates(C.DATE, inplace=True)
        bond = bond.drop_duplicates(C.DATE)

        # 非工作日数据缺失，取前一个工作日的估值
        bond = bond.set_index(C.DATE).resample('D').asfreq().reset_index()
        bond.ffill(inplace=True)

        value_daily = pd.merge(value_daily, bond[[C.DATE, C.VALUE_NET_PRICE]], on=C.DATE, how='left')

        # 如果数据库中没有估值，则默认为100
        value_daily.fillna(100, inplace=True)

        return value_daily

    def _daily_holded_all(self) -> pd.DataFrame:

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

        # 这里不包括委托投资的持仓
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

        if (_self.start_time > _self.end_time or _self.holded_info.empty or
                (bond_code not in _self.holded_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        bond = _self.holded.loc[_self.holded[C.BOND_CODE] == bond_code]

        return bond

    def _request_distributions(self) -> pd.DataFrame:
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
        bonds_group = bonds.groupby([C.DATE, C.BOND_CODE, C.MARKET_CODE, C.DIRECTION, C.BOND_NAME]).agg({

            C.NET_PRICE: lambda x: x.iloc[0],
            C.BOND_AMT_CASH: lambda x: x.sum(),
        })

        return bonds_group

    def _bank_trades(_self) -> pd.DataFrame:

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

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        bank = self._bank_trades()
        exchange = self._exchange_trades()

        if exchange.empty:
            return bank
        else:
            return pd.concat([bank, exchange], ignore_index=True)

    def _capital_all(self) -> pd.DataFrame:

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

        # add one day from the C.DATE column
        holded_copy[C.DATE] = holded_copy[C.DATE] + pd.Timedelta(days=1)

        # Merge raw_group with the modified holded_copy
        raw_group = pd.merge(raw_group,
                             holded_copy[[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME, C.COST_NET_PRICE]],
                             on=[C.DATE, C.BOND_CODE, C.BOND_NAME], how='left')

        # todo 理论上没有空值，但是源数据库数据有问题(20161219,160010)，暂时做此处理
        raw_group[C.COST_NET_PRICE] = raw_group[C.COST_NET_PRICE].fillna(100)
        raw_group[C.CAPITAL_GAINS] = ((raw_group[C.WEIGHT_NET_PRICE] - raw_group[C.COST_NET_PRICE])
                                      * raw_group[C.BOND_AMT_CASH] / 100)

        return raw_group

    def get_capital(self, bond_code: str) -> pd.DataFrame:

        if self.start_time > self.end_time or self.capital.empty or bond_code not in self.capital[C.BOND_CODE].tolist():
            return pd.DataFrame({})

        mask = (self.capital[C.BOND_CODE] == bond_code)
        capital = self.capital.loc[mask, :]

        return capital

    def get_daily_insts(_self, bond_code: str) -> pd.DataFrame:

        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        inst = _self.get_inst_flow(bond_code)

        raw_inst = pd.merge(raw, inst, on=C.DATE, how='left')
        raw_inst[C.INST_A_DAY] = (raw_inst[C.INST_A_DAY] * raw_inst[C.HOLD_AMT] / 100)
        # raw_inst.fillna(0, inplace=True)

        return raw_inst

    def get_net_profit(_self, bond_code: str) -> pd.DataFrame:

        raw = _self.daily_holded_bond(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        value = _self.get_daily_value(bond_code)

        raw_value = pd.merge(raw, value, on=C.DATE, how='left')
        raw_value[C.NET_PROFIT] = (raw_value[C.HOLD_AMT] / 100 *
                                   (raw_value[C.VALUE_NET_PRICE] - raw_value[C.COST_NET_PRICE])).fillna(0)

        return raw_value

    def _holded_bonds_info(self) -> pd.DataFrame:

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

    def sum_all_profits(self, bond_code: str) -> pd.DataFrame:

        if (self.start_time > self.end_time or self.holded_info.empty or
                bond_code not in self.holded_info[C.BOND_CODE].tolist()):
            return pd.DataFrame({})

        # 如果有该债券的持仓，这两项一定不会是空值
        daily_insts = self.get_daily_insts(bond_code)
        net_profit = self.get_net_profit(bond_code)

        bond = self.daily_holded_bond(bond_code).copy()
        capital = self.get_capital(bond_code)

        if capital.empty:

            bond[C.CAPITAL_GAINS] = 0.0
        else:
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
        # 资金占用
        bond[C.CAPITAL_OCCUPY] = bond[C.HOLD_AMT] * bond[C.COST_FULL_PRICE] / 100

        mask = (bond[C.DATE] >= pd.to_datetime(self.start_time)) & (bond[C.DATE] <= pd.to_datetime(self.end_time))
        return bond.loc[mask, :]


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
