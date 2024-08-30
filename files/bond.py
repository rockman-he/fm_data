# Author: RockMan
# CreateTime: 2024/8/15
# FileName: cd
# Description: simple introduction of the code

import pandas as pd
import streamlit as st

from bond_tx import SecurityTx, CDTx, BondTx
from fund_tx import Repo
from utils.web_data import FundDataHandler, SecurityDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts.globals import ThemeType

from utils.txn_factory import TxFactory
from utils.web_view import tx_header, line_global, line_component, bar_global, pie_global
from pyecharts.charts import Line, Bar, Pie
from pyecharts import options as opts

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="同业存单业务",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 债券业务")
st.divider()

txn = None
daily_data = pd.DataFrame({})
daily_data_inst = pd.DataFrame({})

# 按时间段查询的form
with st.form("cd"):
    txn_start_time, txn_end_time, txn_cps_type = st.columns([1, 1, 3])
    with txn_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_month_dates()[1],
            # 要明确每个组件的key，不然会共用一个组件
            key='bond_start_time'
        )

    with txn_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=TimeUtil.get_current_and_last_month_dates()[2],
            key='bond_end_time'
        )

    with txn_cps_type:
        pass

    txn_submit = st.form_submit_button('查  询')

if txn_submit:
    txn = BondTx(start_time, end_time)
    dh = SecurityDataHandler(txn)
    daily_data = dh.daily_yield_all().reset_index()
    daily_data_inst = dh.daily_yield_credit_bond().reset_index()

bond_code = '160017.IB'

if txn is not None:

    st.divider()
    st.write("#### 🥇 每日余额利率情况")
    st.write("###  ")

    st.dataframe(daily_data)
    st.dataframe(daily_data_inst)

    # 创建一个包含从start_time到end_time的所有日期的新的DataFrame
    date_range = pd.date_range(start=start_time, end=end_time)
    df_null = pd.DataFrame(date_range, columns=[C.DATE])

    # 扩充daily_data，使其包含所有的日期
    daily_data_all = pd.merge(df_null, daily_data, on=C.DATE, how='left')
    # 使用fillna函数将所有的缺失值填充为0
    daily_data_all = daily_data_all.fillna(0)

    # 日均余额曲线
    line_amt_all = line_global(daily_data_all, C.DATE, C.HOLD_AMT, "每日持仓（亿元）")
    # 收益率
    line_yield_all = line_component(daily_data_all, C.DATE, C.YIELD, "收益率（%）", color="#FF6347")
    # 收益率不包含净价浮盈
    line_yield_nn_all = line_component(daily_data_all, C.DATE, C.YIELD_NO_NET_PROFIT, "收益率（NN,%）",
                                       color="green")

    streamlit_echarts.st_pyecharts(
        # line_amt.overlap(line_irt).overlap(line_R001).overlap(line_R007),
        line_amt_all.overlap(line_yield_all).overlap(line_yield_nn_all),
        theme=ThemeType.WALDEN,
        height='600px'
    )


else:
    st.divider()
