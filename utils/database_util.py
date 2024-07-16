# Author: RockMan
# CreateTime: 2024/7/15
# FileName: database_util
# Description: This module provides utility functions for database operations.

import streamlit as st


class Constants:
    """
    This class is used to store constant values.
    """

    # ------------------------数据仓库字段------------------------
    # Database connection name
    DATABASE_NAME = 'upsrod'
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


class DatabaseUtil:
    """
    This class is used to handle database connections and queries.
    """

    # A class variable to hold the database connection object.
    __conn = None

    def __init__(self, db_name=Constants.DATABASE_NAME):
        """
        Constructor for the DatabaseUtil class.

        Args:
            db_name (str): The name of the database to connect to. Defaults to Constants.DATABASE_NAME.

        If a connection has not been established yet, it calls the __get_connection method to establish one.
        """
        if DatabaseUtil.__conn is None:
            DatabaseUtil.__conn = self.__get_connection(db_name)

    @st.cache_resource
    def __get_connection(_self, db_name) -> st.connection:
        """
        Private method to establish a connection to the database.

        Args:
            db_name (str): The name of the database to connect to.

        Returns:
            st.connection: A Streamlit connection object.

        This method is decorated with the @st.cache_resource decorator to cache the connection object.
        """
        return st.connection(db_name, type='sql', ttl=600)

    @st.cache_data
    def execute_query(_self, sql) -> st.dataframe:
        """
        Method to execute a SQL query on the connected database.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            st.dataframe: A Streamlit dataframe object containing the result of the query.

        This method is decorated with the @st.cache_data decorator to cache the result of the query.
        """
        return _self.__conn.query(sql)


if __name__ == '__main__':
    db1 = DatabaseUtil()
    db2 = DatabaseUtil()
    _sql = "select * from fm_da.market_irt mi where mi.date between \'2023-01-01\' and \'2023-06-01\';"
    print(db1.execute_query(_sql))
