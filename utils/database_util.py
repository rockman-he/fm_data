# Author: RockMan
# CreateTime: 2024/7/15
# FileName: database_util
# Description: This module provides utility functions for database operations.
# from abc import ABCMeta, abstractmethod
from typing import Dict

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
    # 交易对手
    COUNTERPARTY = 'counterparty'
    # 主机构
    MAIN_ORG = 'mastername'
    # 从机构
    SUB_ORG = 'slavename'
    # 交易方向，正回购为4，逆回购为1
    DIRECTION = 'side'
    # 回购利率
    REPO_RATE = 'reporate'
    # 折算后券面总额
    CONVERTED_BOND_AMOUNT = 'turnover'
    # 券面总额
    BOND_AMOUNT = 'sumunderlyingqty'
    # 回购交易金额
    REPO_AMOUNT = 'tradecashamt'
    # 利息金额
    INTEREST_AMOUNT = 'accruedinterestamt'
    # 首次结算日
    SETTLEMENT_DATE = 'settledate'
    # 到期结算日
    MATURITY_DATE = 'settledate2'
    # 实际占款天数
    CASH_HOLDING_DAYS = 'cashholdingdays'
    # 核对情况
    CHECK_STATUS = 'assignstate'
    # 统计起始时间
    AS_DT = 'as_dt'
    # 统计结束时间
    AE_DT = 'ae_dt'

    # ------------------------自定义市场利率字段------------------------
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
    # 积数
    PRODUCT = 'product'
    # 实际收息
    INST_DAYS = 'inst_days'
    # 每天利息
    INST_A_DAY = 'inst_a_day'
    # 加权利率
    WEIGHT_RATE = 'weight_rate'


class DBUtil:
    """
    This class is used to manage database connections. It uses the Borg design pattern to share state across instances.
    """
    __shared_state: Dict[str, st.connection] = {}  # Shared state across instances

    def __init__(self) -> None:
        """
        Constructor method. It assigns the shared state to the instance's dictionary.
        """
        self.__dict__ = self.__shared_state

    def create_conn(self, db_name=Constants.COMP_DBNAME) -> st.connection:
        """
        This method creates a new database connection if it doesn't exist and returns it.
        If the connection already exists, it simply returns the existing connection.

        Args:
            db_name (str): The name of the database. Defaults to Constants.COMP_DBNAME.

        Returns:
            st.connection: The database connection.
        """
        if not hasattr(self, db_name):
            conn = st.connection(db_name, type='sql', ttl=600)
            setattr(self, db_name, conn)
        return getattr(self, db_name)
