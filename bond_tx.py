# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond_tx
# Description: simple introduction of the code
import datetime

import pandas as pd

from utils.db_util import get_raw, create_conn
from utils.db_util import Constants as C


class BondTx:
    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.conn = create_conn()
        self.trades = self.get_all_trades()
        self.holded_info = self.holded_bonds_info()
        self.insts_flow = self.inst_cash_flow_all()
        self.value = self.daily_value_all()
        self.holded = self.daily_holded_all()
        self.capital = self.get_capital_all()
        self.raw = {}

        # sql = f"select " \
        #       f"cc.{C.CARRY_DATE} as {C.DATE}, " \
        #       f"cc.{C.BOND_NAME}, " \
        #       f"cc.{C.BOND_CODE}, " \
        #       f"cc.{C.MARKET_CODE}, " \
        #       f"bi.{C.BOND_TYPE}, " \
        #       f"cc.{C.HOLD_AMT}, " \
        #       f"cc.{C.COST_NET_PRICE}, " \
        #       f"bv.{C.VALUE_TYPE}, " \
        #       f"bv.{C.VALUE_NET_PRICE}, " \
        #       f"bv.{C.VALUE_FULL_PRICE}, " \
        #       f"bv.{C.ACCRUED_INST}, " \
        #       f"bv.{C.ACCRUED_INST_END} " \
        #       f"from {C.COMP_DBNAME}.core_carrybondholds cc " \
        #       f"left join {C.COMP_DBNAME}.basic_bondvaluations bv " \
        #       f"on date(cc.{C.CARRY_DATE}) = date(bv.{C.DEAL_DATE}) and cc.{C.BOND_CODE} = bv.{C.BOND_CODE} " \
        #       f"left join {C.COMP_DBNAME}.basic_bondbasicinfos bi " \
        #       f"on cc.{C.BOND_CODE} = bi.{C.BOND_CODE} " \
        #       f"where date(cc.{C.CARRY_DATE}) >= '" + \
        #       self.start_time.strftime('%Y-%m-%d') + \
        #       f"' and date(cc.{C.CARRY_DATE}) <= '" + \
        #       self.end_time.strftime('%Y-%m-%d') + \
        #       f"' and cc.{C.CARRY_TYPE} = 3" \
        #       f" order by cc.{C.CARRY_DATE};"

        # sql = f"select " \
        #       f"bb.{C.BOND_CODE}, " \
        #       f"bb.{C.BOND_NAME}, " \
        #       f"bb.{C.INST_START_DATE}, " \
        #       f"bb.{C.INST_END_DATE}, " \
        #       f"bb.{C.ACCRUAL_DAYS}, " \
        #       f"bb.{C.PERIOD_INST} " \
        #       f"from {C.COMP_DBNAME}.basic_bondcashflows bb " \
        #       f"where bb.{C.BOND_CODE} = '160017.IB' " \
        #       f"and date(bb.{C.INST_END_DATE}) >= '" + \
        #       self.start_time.strftime('%Y-%m-%d') + \
        #       f"' and date(bb.{C.INST_START_DATE}) <= '" + \
        #       self.end_time.strftime('%Y-%m-%d') + "'"
        #
        # self.raw = self._get_raw_data(sql)

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        if self.start_time > self.end_time:
            return pd.DataFrame({})

        # 从数据库中获取数据
        raw = get_raw(self.conn, sql)

        return raw

    def get_holded_bonds(self) -> pd.DataFrame:
        return self.holded_info

    def inst_cash_flow_all(self) -> pd.DataFrame:

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

        # if raw.empty:
        #     return pd.DataFrame({})

        return raw

    # CD没有利息，处理方式不一样
    def inst_cash_flow(self, bond_code: str) -> pd.DataFrame:

        # sql = f"select " \
        #       f"bb.{C.BOND_CODE}, " \
        #       f"bb.{C.BOND_NAME}, " \
        #       f"bb.{C.INST_START_DATE}, " \
        #       f"bb.{C.INST_END_DATE}, " \
        #       f"bb.{C.ACCRUAL_DAYS}, " \
        #       f"bb.{C.PERIOD_INST} " \
        #       f"from {C.COMP_DBNAME}.basic_bondcashflows bb " \
        #       f"where bb.{C.BOND_CODE} = '{bond_code}' " \
        #       f"and date(bb.{C.INST_END_DATE}) >= '" + \
        #       self.start_time.strftime('%Y-%m-%d') + \
        #       f"' and date(bb.{C.INST_START_DATE}) <= '" + \
        #       self.end_time.strftime('%Y-%m-%d') + "';"
        #
        # raw = self._get_raw_data(sql)

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

    def daily_value_all(self) -> pd.DataFrame:

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
              (self.start_time - datetime.timedelta(days=15)).strftime('%Y-%m-%d') + \
              f"' and date(bv.{C.DEAL_DATE}) <= '" + \
              (self.end_time + datetime.timedelta(days=15)).strftime('%Y-%m-%d') + \
              f"' order by bv.{C.BOND_CODE}, bv.{C.DEAL_DATE};"

        raw = self._get_raw_data(sql)

        # if raw.empty:
        #     return pd.DataFrame({})

        return raw

    def daily_value(self, bond_code: str) -> pd.DataFrame:

        if (self.start_time > self.end_time or self.holded_info.empty or
                (bond_code not in self.holded_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        # 由于数据库表对于非工作日没有估值，所以查询的时间区间前后各增加15个工作日，避免数据缺失
        # sql = f"select " \
        #       f"bv.{C.DEAL_DATE} as {C.DATE}, " \
        #       f"bv.{C.BOND_NAME}, " \
        #       f"bv.{C.BOND_CODE}, " \
        #       f"bv.{C.VALUE_TYPE}, " \
        #       f"bv.{C.VALUE_NET_PRICE}, " \
        #       f"bv.{C.VALUE_FULL_PRICE} " \
        #       f"from {C.COMP_DBNAME}.basic_bondvaluations bv " \
        #       f"where bv.{C.BOND_CODE} = '{bond_code}'" + \
        #       f" and date(bv.{C.DEAL_DATE}) >= '" + \
        #       (self.start_time - datetime.timedelta(days=15)).strftime('%Y-%m-%d') + \
        #       f"' and date(bv.{C.DEAL_DATE}) <= '" + \
        #       (self.end_time + datetime.timedelta(days=15)).strftime('%Y-%m-%d') + \
        #       f"' order by bv.{C.DEAL_DATE};"
        #
        # raw = self._get_raw_data(sql)

        # date_range = pd.date_range(start=self.start_time, end=self.end_time, freq='D')
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

    def daily_holded_all(self) -> pd.DataFrame:

        if self.start_time > self.end_time or self.holded_info.empty:
            return pd.DataFrame({})

        # 这里不包括委托投资的持仓
        sql = f"select " \
              f"cc.{C.CARRY_DATE} as {C.DATE}, " \
              f"cc.{C.BOND_NAME}, " \
              f"cc.{C.BOND_CODE}, " \
              f"cc.{C.MARKET_CODE}, " \
              f"cc.{C.HOLD_AMT}, " \
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

        # if raw.empty:
        #     return pd.DataFrame({})

        return raw

    def daily_holded(_self, bond_code: str) -> pd.DataFrame:

        if (_self.start_time > _self.end_time or _self.holded_info.empty or
                (bond_code not in _self.holded_info[C.BOND_CODE].tolist())):
            return pd.DataFrame({})

        bond = _self.holded.loc[_self.holded[C.BOND_CODE] == bond_code]

        return bond

        # 如果卖空则没有估值，这种情况的处理？

        # date_range = pd.date_range(start=_self.start_time, end=_self.end_time, freq='D')
        # holding_daily = pd.DataFrame(date_range, columns=[C.DATE])
        # holding_daily = pd.merge(holding_daily, bond[[C.DATE, C.HOLD_AMT, C.COST_NET_PRICE]], on=C.DATE, how='left')
        #
        # holding_daily[C.HOLD_AMT] = holding_daily[C.HOLD_AMT].fillna(0)
        # holding_daily[C.COST_NET_PRICE] = holding_daily[C.COST_NET_PRICE].ffill()
        #
        # # 如果区间中出现卖空的情况，则无持仓的每日持仓成本为上一个持仓日的持仓成本
        # if pd.isna(holding_daily.loc[0, C.COST_NET_PRICE]):
        #     sql = f"select " \
        #           f"cc.{C.CARRY_DATE} as {C.DATE}, " \
        #           f"cc.{C.COST_NET_PRICE} " \
        #           f"from {C.COMP_DBNAME}.core_carrybondholds cc " \
        #           f"where cc.{C.BOND_CODE} = '{bond_code}'" + \
        #           f" and date(cc.{C.CARRY_DATE}) < '" + \
        #           _self.start_time.strftime('%Y-%m-%d') + \
        #           f"' and cc.{C.CARRY_TYPE} = 3 " \
        #           f"order by cc.{C.CARRY_DATE} desc limit 1;"
        #
        #     raw = _self._get_raw_data(sql)
        #
        #     # 如果之前没有持仓，则已经是全量数据，直接返回
        #     if raw.empty:
        #         return holding_daily
        #
        #     last_cost_net_price = raw.loc[0, C.COST_NET_PRICE]
        #     mask = holding_daily[C.COST_NET_PRICE].isna()
        #     holding_daily.loc[mask, C.COST_NET_PRICE] = last_cost_net_price
        #
        # return holding_daily

    # def bank_trade_infos(_self, bond_code: str) -> pd.DataFrame:
    #
    #     sql = f"select " \
    #           f"tc.{C.SETTLEMENT_DATE} as {C.DATE}, " \
    #           f"tc.{C.BOND_NAME}, " \
    #           f"tc.{C.BOND_CODE}, " \
    #           f"tc.{C.DIRECTION}, " \
    #           f"tc.{C.NET_PRICE}, " \
    #           f"tc.{C.YIELD}, " \
    #           f"tc.{C.FULL_PRICE}, " \
    #           f"tc.{C.BOND_AMT_CASH}, " \
    #           f"tc.{C.ACCRUED_INST_CASH}, " \
    #           f"tc.{C.TRADE_AMT}, " \
    #           f"tc.{C.SETTLE_AMT} " \
    #           f"from {C.COMP_DBNAME}.trade_cashbonds tc " \
    #           f"where tc.{C.BOND_CODE} = '{bond_code}'" + \
    #           f" and date(tc.{C.TRADE_TIME}) >= '" + \
    #           _self.start_time.strftime('%Y-%m-%d') + \
    #           f"' and date(tc.{C.TRADE_TIME}) <= '" + \
    #           _self.end_time.strftime('%Y-%m-%d') + \
    #           f"' and tc.{C.CHECK_STATUS} = 1 " \
    #           f"order by tc.{C.TRADE_TIME};"
    #
    #     return _self._get_raw_data(sql)

    def request_distributions(self) -> pd.DataFrame:
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
            # C.MARKET_CODE: lambda x: x.iloc[0],
            # C.DIRECTION: lambda x: x.iloc[0],
            C.NET_PRICE: lambda x: x.iloc[0],
            C.BOND_AMT_CASH: lambda x: x.sum(),
        })

        return bonds_group

    def bank_trades(_self) -> pd.DataFrame:

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

    def exchange_trades(self) -> pd.DataFrame:

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

    def get_all_trades(self) -> pd.DataFrame:

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        bank = self.bank_trades()
        exchange = self.exchange_trades()

        return pd.concat([bank, exchange], ignore_index=True)

    def get_capital_all(self) -> pd.DataFrame:

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

        # 理论上没有空值，但是源数据库数据有问题，暂时做此处理
        raw_group[C.COST_NET_PRICE] = raw_group[C.COST_NET_PRICE].fillna(100)

        # raw_group = pd.merge(raw_group, self.holded[[C.DATE, C.BOND_CODE, C.BOND_NAME, C.COST_NET_PRICE]],
        #                      on=[C.DATE, C.BOND_CODE, C.BOND_NAME], how='left')
        #
        # raw_group_none = raw_group.loc[pd.isna(raw_group[C.COST_NET_PRICE]), :]
        #
        # if raw_group_none.empty is False:
        #     for row in raw_group_none.index:
        #         code = raw_group_none.loc[row, C.BOND_CODE]
        #         bond = self.holded.loc[self.holded[C.BOND_CODE] == code, [C.DATE, C.COST_NET_PRICE]]
        #         mask = bond[C.DATE] < raw_group_none.loc[row, C.DATE]
        #         last_value = bond.loc[mask, C.COST_NET_PRICE].tail(1)
        #         # mask = self.holded.loc[self.holded[C.BOND_CODE] == code, C.DATE]
        #         # print(mask)
        #         # previous = self.holded.loc[mask, C.COST_NET_PRICE]
        #         # print(previous.iloc[0])
        #         raw_group_none.loc[row, C.COST_NET_PRICE] = last_value.iloc[0]
        #
        #     # print(raw_group_none)
        #     #
        #     # # raw_group = pd.merge(raw_group, raw_group_none[[C.DATE, C.COST_NET_PRICE]], on=C.DATE, how='left')
        #     raw_group = pd.merge(raw_group, raw_group_none[[C.DATE, C.BOND_CODE, C.COST_NET_PRICE]],
        #                          on=[C.DATE, C.BOND_CODE], how='left', suffixes=('', '_NONE'))
        #     #
        #     # print(raw_group)
        #     col = C.COST_NET_PRICE + '_NONE'
        #     mask = pd.isna(raw_group.loc[:, col])
        #     raw_group.loc[~mask, C.COST_NET_PRICE] = raw_group.loc[~mask, col]
        # #
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

        # if (_self.start_time > _self.end_time or _self.holded_info.empty or
        #         bond_code not in _self.holded_info[C.BOND_CODE].tolist()):
        #     return pd.DataFrame({})
        #
        # mask = (_self.holded[C.BOND_CODE] == bond_code)
        # raw = _self.holded.loc[mask, :]

        raw = _self.daily_holded(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        inst = _self.inst_cash_flow(bond_code)

        raw_inst = pd.merge(raw, inst, on=C.DATE, how='left')
        raw_inst[C.INST_A_DAY] = (raw_inst[C.INST_A_DAY] * raw_inst[C.HOLD_AMT] / 100)
        # raw_inst.fillna(0, inplace=True)

        return raw_inst

    def get_net_profit(_self, bond_code: str) -> pd.DataFrame:

        # if (_self.start_time > _self.end_time or _self.holded_info.empty or
        #         bond_code not in _self.holded_info[C.BOND_CODE].tolist()):
        #     return pd.DataFrame({})
        #
        # mask = (_self.holded[C.BOND_CODE] == bond_code)
        # raw = _self.holded.loc[mask, :]

        raw = _self.daily_holded(bond_code)

        if raw.empty:
            return pd.DataFrame({})

        value = _self.daily_value(bond_code)

        raw_value = pd.merge(raw, value, on=C.DATE, how='left')
        raw_value[C.NET_PROFIT] = (raw_value[C.HOLD_AMT] / 100 *
                                   (raw_value[C.VALUE_NET_PRICE] - raw_value[C.COST_NET_PRICE])).fillna(0)

        return raw_value

    def holded_bonds_info(self) -> pd.DataFrame:

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

        bond = self.daily_holded(bond_code).copy()
        capital = self.get_capital(bond_code)

        # if self.capital.empty is False:
        #     mask = (self.capital[C.BOND_CODE] == bond_code)
        #     capital = self.capital.loc[mask, :]

        if capital.empty:
            # bond.loc[:, C.CAPITAL_GAINS] = 0
            bond[C.CAPITAL_GAINS] = 0.0
        else:
            bond = pd.merge(bond, capital[[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME, C.CAPITAL_GAINS]],
                            on=[C.DATE, C.BOND_CODE, C.MARKET_CODE, C.BOND_NAME], how='outer')
            bond[C.CAPITAL_GAINS] = bond[C.CAPITAL_GAINS].fillna(0)
        bond = pd.merge(bond, daily_insts[[C.DATE, C.INST_A_DAY]], on=C.DATE, how='left')
        bond = pd.merge(bond, net_profit[[C.DATE, C.VALUE_NET_PRICE, C.NET_PROFIT]], on=C.DATE, how='left')

        # 找出包含缺失值的列
        columns_with_none = bond.columns[bond.isna().any()]
        # 对这些列中的缺失值赋值为 0
        bond[columns_with_none] = bond[columns_with_none].astype(float).fillna(0)
        # 计算总收益
        bond[C.TOTAL_PROFIT] = bond[C.CAPITAL_GAINS] + bond[C.INST_A_DAY] + bond[C.NET_PROFIT]

        return bond
