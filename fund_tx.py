# Author: RockMan
# CreateTime: 2024/7/15
# FileName: transaction
# Description: This module contains classes for handling transactions.
import datetime
import pandas as pd

from utils.db_util import Constants as C, create_conn, get_raw


class FundTx:
    """
    这是一个用于 repo 和 ibo 交易的抽象基类。Repo和IBO类继承自该类。

    Attributes:
        start_time (datetime.date): 交易开始时间.
        end_time (datetime.date): 交易截止统计时间（含）.
        inst_base (int): 计息计算基数.
        raw (pd.DataFrame): 交易数据.
    """

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        """
        FundTx的构造函数，计息基数为365

        Args:
            start_time (datetime.date): 交易的开始时间.
            end_time (datetime.date): 交易截止统计时间（含）.
        """
        self.start_time = start_time
        self.end_time = end_time
        # self.direction = direction
        self.inst_base = 365
        self.raw = None
        # self.conn = create_conn()

        # 测试

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        从数据库获取原始数据.

        Args:
            sql (str): sql语句.

        Returns:
            pd.DataFrame: 数据库获取的交易数据.
        """

        # 如果用户选择的截止统计时间晚于起始时间，则返回空df
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

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(raw)

        return raw

    def daily_data(self, direction: int) -> pd.DataFrame:
        """
        获取统计区间内每日持仓的统计数据.

        :param direction: 交易方向，资金融入4，资金融出1

        Returns:
            pd.DataFrame: [AS_DT, C.TRADE_AMT, C.INST_DAYS, C.WEIGHT_RATE]

        """

        if self.raw.empty:
            return pd.DataFrame({})

        r = self.raw.loc[self.raw[C.DIRECTION] == direction, :]

        if r.empty:
            return r

        date_range = pd.date_range(start=self.start_time, end=self.end_time, freq='D')
        daily = pd.DataFrame(date_range, columns=[C.AS_DT])
        daily[C.TRADE_AMT] = 0.0
        daily[C.INST_DAYS] = 0.0

        # 遍历数据库查询结果
        for row in r.index:
            # 回购金额
            trade_amt = r.loc[row, C.TRADE_AMT]
            # 满足统计区间的起始时间
            as_date = r.loc[row, C.AS_DT]
            # 满足统计区间的截止统计时间
            ae_date = r.loc[row, C.AE_DT]
            # 每天的利息
            inst_a_day = r.loc[row, C.INST_A_DAY]

            # 将起止时间段的余额和利息总额进行汇总
            mask = (daily[C.AS_DT] >= as_date) & (daily[C.AS_DT] < ae_date)
            daily.loc[mask, [C.TRADE_AMT]] += trade_amt
            daily.loc[mask, [C.INST_DAYS]] += inst_a_day

        daily[C.WEIGHT_RATE] = daily[C.INST_DAYS] * self.inst_base / daily[C.TRADE_AMT] * 100
        daily[C.WEIGHT_RATE] = daily[C.WEIGHT_RATE].fillna(0)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(daily)

        return daily

    def daily_data_by_direction(self, direction: str) -> pd.DataFrame:

        """
        按交易方向分类源数据.

        Args:
            direction (str): 交易方向['正回购', '逆回购','同业拆入','同业拆出'].

        Returns:
            pd.DataFrame: [AS_DT, C.TRADE_AMT, C.INST_DAYS, C.WEIGHT_RATE]
        """

        pass

    def raw_by_direction(self, direction: int) -> pd.DataFrame:
        """
        按交易方向分类源数据.

        Args:
            direction (int): 交易方向.

        Returns:

        """

        if self.raw.empty:
            return pd.DataFrame({})

        return self.raw.loc[self.raw[C.DIRECTION] == direction]

    def groupby_column(self, column: str, direction: int) -> pd.DataFrame:
        """
        将原始数据按照特定列group聚合.

        Args:
            column (str): 被聚合的列.
            direction(int): 交易方向，资金融入4，资金融出1

        Returns:
            pd.DataFrame: [column, C.AVG_AMT, C.INST_GROUP, C.PRODUCT, C.WEIGHT_RATE].
        """

        raw = self.raw_by_direction(direction)

        # 按列进行分组
        txn_group = raw.groupby(raw[column])
        # 利息加总
        inst_group = txn_group[C.INST_DAYS].agg("sum")
        # 积数加总
        product_group = txn_group[C.PRODUCT].agg("sum")
        # 加权利率
        weight_rate = inst_group * self.inst_base / product_group * 100
        # 计算日均余额
        avg_amt = product_group / ((self.end_time - self.start_time).days + 1)
        # 分组后按日均余额升序排列
        column_type = pd.DataFrame({C.AVG_AMT: avg_amt,
                                    C.INST_GROUP: inst_group,
                                    C.PRODUCT: product_group,
                                    C.WEIGHT_RATE: weight_rate})
        column_type.sort_values(by=C.AVG_AMT, ascending=False, inplace=True)
        column_type.reset_index(inplace=True)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(term_type)

        return column_type


class Repo(FundTx):
    """
    回购交易类.

    Attributes:
        start_time (datetime.date): 交易的开始统计时间.
        end_time (datetime.date): 交易截止统计时间（含）.
    """

    # TODO 还缺少买断式回购、交易所回购的统计，同时要补全机构的code
    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        """
        构造函数.

        Args:
            start_time (datetime.date): 交易的开始统计时间.
            end_time (datetime.date): 交易截止统计时间（含）.
        """

        super().__init__(start_time, end_time)

        # self.direction = '4' if self.direction == '正回购' else '1'
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
              f" order by tc.{C.SETTLEMENT_DATE};"
        # f" and tc.{C.DIRECTION} = " + self.direction + \

        self.raw = self._get_raw_data(sql)

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        从数据库获取原始数据.

        Args:
            sql (str): sql语句.

        Returns:
            pd.DataFrame: 数据库获取的交易数据.
        """

        raw = super()._get_raw_data(sql)

        if raw.empty:
            return pd.DataFrame({})

        # 如果主机构为空，则用子机构的名称代替
        mask = raw[C.NAME].isnull()
        raw.loc[mask, C.NAME] = raw.loc[mask, C.COUNTERPARTY]

        return raw


class IBO(FundTx):

    def __init__(self, start_time: datetime.date, end_time: datetime.date) -> None:
        """
        构造函数.

        Args:
            start_time (datetime.date): 交易的开始统计时间.
            end_time (datetime.date): 交易截止统计时间（含）.
        """

        super().__init__(start_time, end_time)
        self.inst_base = 360
        # self.direction = '1' if self.direction == '同业拆入' else '4'

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
              f" order by ti.{C.SETTLEMENT_DATE};"
        # f" and ti.{C.DIRECTION} = " + self.direction + \

        self.raw = self._get_raw_data(sql)

        # 拆借业务的原数据融入融出代码与回购相反，这里做一个统一
        if not self.raw.empty:
            self.raw[C.DIRECTION] = self.raw[C.DIRECTION].replace({4: 1, 1: 4})

    def _get_raw_data(self, sql: str) -> pd.DataFrame:
        """
        从数据库获取原始数据.

        Args:
            sql (str): sql语句.

        Returns:
            pd.DataFrame: 数据库获取的交易数据.
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
    s_t = datetime.date(2023, 11, 14)
    e_t = datetime.date(2023, 11, 20)
    repo = Repo(s_t, e_t)
