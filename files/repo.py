# Author: RockMan
# CreateTime: 2024/7/15
# FileName: repo.py
# Description: 用于展示回购交易要素的页面
import pandas as pd
import streamlit as st

from fund_tx import Repo
from utils.web_data import WebDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts.globals import ThemeType

from utils.txn_factory import TxFactory
from utils.web_view import tx_header, line_global, line_component, bar_global, pie_global

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="回购业务",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 回购业务")
st.divider()

# 按时间段查询的form
with st.form("tx"):
    txn_start_time, txn_end_time, txn_cps_type = st.columns([1, 1, 3])
    with txn_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_month_dates()[1],
            # 要明确每个组件的key，不然会共用一个组件
            key='txn_start_time'
        )

    with txn_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=TimeUtil.get_current_and_last_month_dates()[2],
            key='txn_end_time'
        )

    with txn_cps_type:
        cps_type = st.selectbox(
            '业务类型',
            ('正回购', '逆回购'),
            key='txn_cps_type'
        )

    txn_submit = st.form_submit_button('查  询')

dh = {'party': pd.DataFrame({})}

if txn_submit:
    txn = TxFactory(Repo).create_txn(start_time, end_time, cps_type)
    dh = WebDataHandler(txn).get_txn_header()

if (dh['party']).empty:
    st.write("无数据")
else:

    tx_header(dh)

    st.divider()
    st.markdown("#### 🥇 每日余额利率情况")
    st.write("###  ")

    # 回购业务的日均余额曲线
    line_amt = line_global(dh['daily'], C.AS_DT, C.TRADE_AMT, "日均余额（亿元）")

    # 回购业务的加权利率曲线
    line_irt = line_component(dh['daily'], C.AS_DT, C.WEIGHT_RATE, '加权利率（%）', 'red')

    # 资金市场R001利率曲线
    line_R001 = line_component(dh['daily'], C.AS_DT, C.R001, C.R001, 'green')

    # 资金市场R007利率曲线
    line_R007 = line_component(dh['daily'], C.AS_DT, C.R007, C.R007, 'purple')

    streamlit_echarts.st_pyecharts(
        line_amt.overlap(line_irt).overlap(line_R001).overlap(line_R007),
        theme=ThemeType.WALDEN,
        height='500px'
    )

    st.divider()
    st.markdown("#### 🚒 交易对手排名")
    st.markdown(" ")

    bar_party = bar_global(dh['partyn_total'], C.NAME,
                           '日均余额(亿元）', C.AVG_AMT, '加权利率（%）', C.WEIGHT_RATE)

    streamlit_echarts.st_pyecharts(
        bar_party,
        theme=ThemeType.WALDEN,
        height='800px',
        # width='75%'
    )

    st.divider()
    st.markdown("#### ⛪ 交易对手占比")
    st.markdown(" ")

    pie_party = pie_global(dh['party_n'], C.NAME, C.AVG_AMT, '日均余额(亿元）')

    streamlit_echarts.st_pyecharts(
        pie_party,
        theme=ThemeType.WALDEN,
        # height='800px',
        # width='50%'
    )

    with st.expander("交易对手明细(全量）"):

        if dh['party_total'].empty is False:
            # 对输出格式化
            txn_party_total = WebDataHandler.format_output(dh['party_total'])

        st.dataframe(txn_party_total[[C.NAME, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.NAME: '交易对手',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })

    st.divider()
    st.markdown("#### 🪟 期限分析")
    st.write("###  ")

    pie_term = pie_global(dh['term'], C.TERM_TYPE, C.AVG_AMT, '日均余额（亿元）')

    streamlit_echarts.st_pyecharts(
        pie_term,
        theme=ThemeType.WALDEN,
    )

    with st.expander("期限占比明细"):
        if dh['term_total'].empty is False:
            # 对输出格式化
            txn_term_total = WebDataHandler.format_output(dh['term_total'])

        st.dataframe(txn_term_total[[C.TERM_TYPE, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.TERM_TYPE: '期限类别',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })
