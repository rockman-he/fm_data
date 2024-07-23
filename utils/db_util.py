# Author: RockMan
# CreateTime: 2024/7/19
# FileName: db.util
# Description: simple introduction of the code
# from typing import Dict

import pandas as pd
import streamlit as st


class Constants:
    """
    This class is used to store constant values.
    """

    # ------------------------数据仓库字段------------------------
    # Database connection name
    COMP_DBNAME = 'upsrod'
    # 成交单编号
    TRADE_NO = 'execid'
    # 期限种类
    TERM_TYPE = 'securityid'
    # 本方交易员
    TRADER = 'selfquotername'
    # 机构代码
    CODE = 'code'
    # 交易对手
    COUNTERPARTY = 'counterparty'
    # 机构简称
    SHORT_NAME = 'shortname'
    # 机构全称
    NAME = 'name'
    # 主机构，在Repo中标准化为NAME
    MAIN_ORG = 'mastername'
    # 从机构
    SUB_ORG = 'slavename'
    # 交易方向，正回购为4，逆回购为1
    DIRECTION = 'side'
    # 回购利率，在Repo中标准化为RATE
    REPO_RATE = 'reporate'
    # 拆借利率，在IBO中标准化为RATE
    IBO_RATE = 'iborate'
    # 折算后券面总额
    CONVERTED_BOND_AMOUNT = 'turnover'
    # 券面总额
    BOND_AMOUNT = 'sumunderlyingqty'
    # 回购交易金额，在Repo中标准化为TRADE_AMT
    REPO_AMOUNT = 'tradecashamt'
    # 拆借交易金额，在IBO中标准化为TRADE_AMT
    IBO_AMOUNT = 'turnover'
    # 利息金额
    INTEREST_AMOUNT = 'accruedinterestamt'
    # 首次结算日
    SETTLEMENT_DATE = 'settledate'
    # 到期结算日
    MATURITY_DATE = 'settledate2'
    # 实际占款天数
    HOLDING_DAYS = 'cashholdingdays'
    # 核对情况
    CHECK_STATUS = 'assignstate'

    # ------------------------自定义市场利率字段------------------------

    # 统计起始时间
    AS_DT = 'as_dt'
    # 统计结束时间
    AE_DT = 'ae_dt'

    # 日期
    DATE = 'date'
    # R001
    R001 = 'R001'
    # R007
    R007 = 'R007'
    # SHIBOR_O/N
    SHIBOR_ON = 'Shibor(O/N)'
    # SHIBOR_1W
    SHIBOR_1W = 'Shibor(1W)'

    # ------------------------自定义中间字段------------------------
    # 统计天数
    WORK_DAYS = 'work_days'
    # 交易金额
    TRADE_AMT = 'trade_amt'
    # 积数
    PRODUCT = 'product'
    # 实际收息
    INST_DAYS = 'inst_days'
    # 每天利息
    INST_A_DAY = 'inst_a_day'
    # 分组后的利息
    INST_GROUP = 'inst_group'
    # 加权利率
    WEIGHT_RATE = 'weight_rate'
    # 日均余额
    AVG_AMT = 'avg_amt'
    # 交易笔数
    TRADE_NUM = 'trade_num'
    # 交易总额（按发生）
    TRADE_SUM = 'trade_sum'
    # 交易金额（按加权）
    TRADE_WEIGHT_SUM = 'trade_weight'
    # 利率
    RATE = 'rate'
    # 最高利率
    MAX_RATE = 'max_rate'
    # 最低利率
    MIN_RATE = 'min_rate'


@st.cache_resource
def create_conn(db=Constants.COMP_DBNAME):
    """
    Create a connection to the database.
    :param db: Database name
    :return: Connection object
    """
    return st.connection(db, type='sql', ttl=600)


@st.cache_data
def get_raw(_conn: st.connection, sql: str) -> pd.DataFrame:
    return _conn.query(sql)
