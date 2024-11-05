# Author: RockMan
# CreateTime: 2024/7/19
# FileName: db_util
# Description: This module provides utility functions for database operations.

import pandas as pd
import streamlit as st


class Constants:
    """
    项目用到的常量
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
    # 交易方向（一级）
    DIRECTION2 = 'dealside'
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
    # 交易日期
    TRADE_DATE = 'tradedate'
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
    # 成本全价
    COST_FULL_PRICE = 'costdrtprc'
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
    # 净价（一级）
    NET_PRICE2 = 'cleanprice'
    # 收益率
    YIELD = 'yield'
    # 收益率累加
    YIELD_CUM = 'yield_cum'
    # 收益率不包括净价浮盈
    YIELD_NO_NET_PROFIT = 'yield_no_net_profit'
    # 全价
    FULL_PRICE = 'drtprc'
    # 券面总额（现券交易，银行间）
    BOND_AMT_CASH = 'lastqty'
    # 券面总额（现券交易，交易所）
    BOND_AMT_CASH2 = 'faceamt'
    # 应计利息总额（现券买卖，银行间）
    ACCRUED_INST_CASH = 'totacruamt'
    # 应计利息总额（现券买卖，交易所）
    ACCRUED_INST_CASH2 = 'totalaiamt'
    # 交易金额（现券买卖）
    TRADE_AMT = 'tradecashamt'
    # 结算金额（现券买卖）
    SETTLE_AMT = 'settlecurramt'
    # 成交状态
    TRADE_STATUS = 'status'
    # 交易加权净价
    WEIGHT_NET_PRICE = 'tradeweightclnprc'
    # 组合编号
    PORTFOLIO_NO = 'portfoliono'
    # 交易类型，一级或者二级
    TRADE_TYPE = 'tradetype'

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
    # 资本利得累加
    CAPITAL_GAINS_CUM = 'capital_gains_cum'
    # 净价浮盈
    NET_PROFIT = 'net_profit'
    # 净价浮盈减期初
    NET_PROFIT_SUB = 'net_profit_sub'
    # 前一天的成本净价
    LAST_COST_NET_PRICE = 'last_cost_net_price'
    # 总收益
    TOTAL_PROFIT = 'total_profit'
    # 区间总收益
    TOTAL_PROFIT_CUM = 'total_profit_cum'
    # 资金占用
    CAPITAL_OCCUPY = 'capital_occupy'
    # 累计资金占用
    CAPITAL_OCCUPY_CUM = 'capital_occupy_cum'
    # 托管市场（利率债，信用债）
    BOND_CUST = 'bond_cust'
    # 利率债代码
    INST_BOND_NUM = {0, 1, 6, 11}


@st.cache_resource
def create_conn(db=Constants.COMP_DBNAME) -> st.connection:
    """
    建立一个数据库对象

    :param db: 数据库名，默认为'upsrod'
    :return: 数据库对象
    """
    return st.connection(db, type='sql', ttl=600, max_entries=40)


@st.cache_data
def get_raw(_conn: st.connection, sql: str) -> pd.DataFrame:
    """
    从数据库中查询数据

    :param _conn: 数据库对象
    :param sql: SQL查询语句
    :return: 查询到的数据
    """

    return _conn.query(sql)
