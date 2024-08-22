# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond
# Description: simple introduction of the code

import pandas as pd
import streamlit as st

from bond_tx import BondTx
from fund_tx import Repo
from utils.web_data import WebDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts.globals import ThemeType

from utils.txn_factory import TxFactory
from utils.web_view import tx_header, line_global, line_component, bar_global, pie_global

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="数据测试",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 数据测试")
st.divider()

txn = None

# 按时间段查询的form
with st.form("test"):
    txn_start_time, txn_end_time, txn_cps_type = st.columns([1, 1, 3])
    with txn_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_month_dates()[1],
            # 要明确每个组件的key，不然会共用一个组件
            key='test_start_time'
        )

    with txn_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=TimeUtil.get_current_and_last_month_dates()[2],
            key='test_end_time'
        )

    with txn_cps_type:
        pass

    txn_submit = st.form_submit_button('查  询')

if txn_submit:
    txn = BondTx(start_time, end_time)

# st.write('利息现金流')
# df1 = txn.inst_cash_flow(bond_code)
# st.dataframe(df1)
#
# st.write('债券估值')
# df2 = txn.daily_value(bond_code)
# st.dataframe(df2)
#
# st.write('交易明细')
# df3 = txn.bank_trade_infos(bond_code)
# st.dataframe(df3, use_container_width=True)
#
# st.write('持仓明细')
# df4 = txn.daily_holding(bond_code)
# st.dataframe(df4, use_container_width=True)
#
# st.write('资本利得')
# df5 = txn.get_capital_gains(bond_code)
# st.dataframe(df5, use_container_width=True)
#
# st.write('每日利息')
# df6 = txn.get_daily_insts(bond_code)
# st.dataframe(df6, use_container_width=True)
#
# st.write('净价浮盈')
# df7 = txn.get_net_profit(bond_code)
# st.dataframe(df7, use_container_width=True)
#
# st.write('持仓债券基础信息')

if txn is not None:

    st.write('## 债券业务')
    st.divider()

    st.write('持仓债券基础信息')
    df8 = txn.get_bond()
    st.dataframe(df8)

    bond_list = df8[C.BOND_CODE].tolist()
    list = {}
    for i in range(len(bond_list)):
        bond_code = bond_list[i]
        list[bond_code] = txn.sum_all(bond_code)

    for i in list:
        st.write(i)
        st.dataframe(list[i], use_container_width=True)
