# Author: RockMan
# CreateTime: 2024/7/19
# FileName: db_util
# Description: This module provides utility functions for database operations.

import pandas as pd
import streamlit as st


class Constants:
    """
    This class is used to store constant values related to database fields and custom fields for projects.
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
    CONVERTED_BOND_AMT = 'turnover'
    # 券面总额（质押）
    BOND_AMT = 'sumunderlyingqty'
    # 回购交易金额，在Repo中标准化为TRADE_AMT
    REPO_AMT = 'tradecashamt'
    # 拆借交易金额，在IBO中标准化为TRADE_AMT
    IBO_AMT = 'turnover'
    # 利息金额
    INTEREST_AMT = 'accruedinterestamt'
    # 首次结算日
    SETTLEMENT_DATE = 'settledate'
    # 到期结算日
    MATURITY_DATE = 'settledate2'
    # 实际占款天数
    HOLDING_DAYS = 'cashholdingdays'
    # 核对情况
    CHECK_STATUS = 'assignstate'
    # 结转日期
    CARRY_DATE = 'carrydate'
    # 债券名称
    BOND_NAME = 'bondname'
    # 债券全程
    BOND_FULL_NAME = 'secname'
    # 债券代码
    BOND_CODE = 'bondkey'
    # 市场代码
    MARKET_CODE = 'marketcode'
    # 债券类型
    BOND_TYPE = 'l2sectype'
    # 债券类型（数字）
    BOND_TYPE_NUM = 'sectype'
    # 债券发行日
    ISSUE_DATE = 'issuedate'
    # 债券到期日
    MATURITY = 'matdate'
    # 票面利率（当期）
    COUPON_RATE_CURRENT = 'cpnrate_current'
    # 票面利率（发行）
    COUPON_RATE_ISSUE = 'cpnrate_issue'
    # 发行量
    ISSUE_AMT = 'issuesize'
    # 发行价格
    ISSUE_PRICE = 'issueprice'
    # 发行机构
    ISSUE_ORG = 'issuername'
    # 债券期限
    BOND_TERM = 'term'
    # 持仓面额
    HOLD_AMT = 'holdfaceamt'
    # 成本净价
    COST_NET_PRICE = 'costclnprc'
    # 估值方式，Mat：到期值，Option：行权值
    VALUE_TYPE = 'cdctype'
    # 估值净价
    VALUE_NET_PRICE = 'suggest_cleanprice_mdl'
    # 估值全价
    VALUE_FULL_PRICE = 'suggest_dirtyprice_mdl'
    # 日初应计利息
    ACCRUED_INST = 'accruedinterest'
    # 日终应计利息
    ACCRUED_INST_END = 'accruedinterestendday'
    # 估值日期
    DEAL_DATE = 'dealdate'
    # 结转类型
    CARRY_TYPE = 'carrytype'
    # 利息开始日期
    INST_START_DATE = 'intereststartdate'
    # 利息结束日期
    INST_END_DATE = 'interestenddate'
    # 计息天数
    ACCRUAL_DAYS = 'interestdays'
    # 当期利息总额
    PERIOD_INST = 'interestamt'
    # 成交时间
    TRADE_TIME = 'tradetime'
    # 净价
    NET_PRICE = 'clnprc'
    # 收益率
    YIELD = 'yield'
    # 全价
    FULL_PRICE = 'drtprc'
    # 券面总额（现券交易）
    BOND_AMT_CASH = 'lastqty'
    # 应计利息总额（现券买卖）
    ACCRUED_INST_CASH = 'totacruamt'
    # 交易金额（现券买卖）
    TRADE_AMT = 'tradecashamt'
    # 结算金额（现券买卖）
    SETTLE_AMT = 'settlecurramt'
    # 成交状态
    TRADE_STATUS = 'status'
    # 交易加权净价
    WEIGHT_NET_PRICE = 'tradeweightclnprc'

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
    # TRADE_AMT = 'trade_amt'
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
    # 资本利得
    CAPITAL_GAINS = 'capital_gains'
    # 净价浮盈
    NET_PROFIT = 'net_profit'
    # 前一天的成本净价
    LAST_COST_NET_PRICE = 'last_cost_net_price'
    # 总收益
    TOTAL_PROFIT = 'total_profit'


@st.cache_resource
def create_conn(db=Constants.COMP_DBNAME) -> st.connection:
    """
    Create a connection to the database.

    :param db: Database name, defaults to 'upsrod'
    :return: Connection object
    """
    return st.connection(db, type='sql', ttl=600, max_entries=20)


@st.cache_data
def get_raw(_conn: st.connection, sql: str) -> pd.DataFrame:
    """
    Query raw data from the database.

    :param _conn: Database connection object
    :param sql: SQL query string
    :return: DataFrame containing the queried data
    """
    return _conn.query(sql)
