# Author: RockMan
# CreateTime: 2024/8/15
# FileName: cd
# Description: simple introduction of the code
import numpy as np
import pandas as pd
import streamlit as st
from pyecharts.charts.chart import RectChart
from pyecharts.options import LabelOpts

from bond_tx import SecurityTx, CDTx, BondTx
from fund_tx import Repo
from utils.web_data import FundDataHandler, SecurityDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C
import altair as alt

import streamlit_echarts
from pyecharts.globals import ThemeType

from utils.txn_factory import TxFactory
from utils.web_view import fund_tx_header, fund_line_global, line_component, bar_global, pie_global, security_line
from pyecharts.charts import Grid, Bar, Line
from pyecharts import options as opts
from streamlit.components.v1 import html

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="债券业务",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 债券业务")
st.divider()

txn = None
dh = None
# 按时间段查询的form
with st.form("bond"):
    txn_start_time, txn_end_time, txn_cps_type = st.columns([1, 1, 3])
    with txn_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_year()[0],
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

bond_code = '160017.IB'

if txn is not None:

    if not dh.get_raw().empty:
        st.divider()

        st.write("#### 区间收益")
        st.write("###  ")

        # streamlit_echarts.st_pyecharts(
        #     security_line(daily_all_cum),
        #     # c,
        #     theme=ThemeType.WALDEN,
        #     height='700px'
        # )

        # st.expander('详细数据').write(daily_all_cum.loc[daily_all_cum[C.HOLD_AMT] != 0, :])
        # st.expander('详细数据').write(daily_all_cum)

        tab1, tab2, tab3 = st.tabs(["全部债券", "利率债", "信用债"])

        with tab1:
            daily_all_cum = dh.daily_yield_all_cum(start_time, end_time)

            # temp1 = streamlit_echarts.st_pyecharts(
            #     chart=security_line(daily_all_cum),
            #     # c,
            #     theme=ThemeType.WALDEN,
            #     height='700px',
            #     key='all'
            # )
            # tab1.write(temp1)

            # chart = security_line(daily_all_cum).render_embed()
            html(security_line(daily_all_cum).render_embed(), height=800)

        with tab2:
            daily_inst_cum = dh.daily_yield_inst_cum(start_time, end_time)
            # chart = security_line(daily_inst_cum).render_embed()
            html(security_line(daily_inst_cum).render_embed(), height=800)

        with tab3:
            daily_credit_cum = dh.daily_yield_credit_cum(start_time, end_time)
            # chart = security_line(daily_inst_cum).render_embed()
            html(security_line(daily_credit_cum).render_embed(), height=800)


else:
    st.divider()
