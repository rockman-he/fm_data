# Author: RockMan
# CreateTime: 2024/7/15
# FileName: 1_🏻_拆借业务.py
# Description: 用于展示拆借交易要素的页面

import pandas as pd
import streamlit as st

from fund_tx import IBO
from utils.web_data import FundDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts.globals import ThemeType

from utils.txn_factory import TxFactory
from utils.web_view import fund_tx_header, fund_line_global, line_component, bar_global, pie_global

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="拆借业务",
                   page_icon="🏻",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("##  拆借业务")
st.divider()

# 按时间段查询的form
with st.form("ibo"):
    ibo_start_time, ibo_end_time, ibo_cps_type = st.columns([1, 1, 3])
    with ibo_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_month_dates()[1],
            # 要明确每个组件的key，不然会共用一个组件
            key='ibo_start_time'
        )

    with ibo_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=TimeUtil.get_current_and_last_month_dates()[2],
            key='ibo_end_time'
        )

    with ibo_cps_type:
        cps_type = st.selectbox(
            '业务类型',
            ('同业拆入', '同业拆出'),
            key='ibo_cps_type'
        )

    txn_submit = st.form_submit_button('查  询')

dh = {'party': pd.DataFrame({})}

if txn_submit:
    txn = TxFactory(IBO).create_txn(start_time, end_time, cps_type)
    dh = FundDataHandler(txn).get_txn_header()

if (dh['party']).empty:
    st.write("无数据")
else:

    # 显示交易统计信息
    fund_tx_header(dh)

    st.divider()
    st.markdown("###  每日余额利率情况")
    st.write("###  ")

    # 拆借业务的日均余额曲线
    line_amt = fund_line_global(dh['holded'], C.AS_DT, C.TRADE_AMT, "日均余额（亿元）")

    # 拆借业务的加权利率曲线
    line_irt = line_component(dh['holded'], C.AS_DT, C.WEIGHT_RATE, '加权利率（%）', 'red')

    # 资金市场Shibor(O/ N)利率曲线
    line_shibor_on = line_component(dh['holded'], C.AS_DT, C.SHIBOR_ON, C.SHIBOR_ON, 'green')

    # 资金市场Shibor(1W)利率曲线
    line_shibor_1w = line_component(dh['holded'], C.AS_DT, C.SHIBOR_1W, C.SHIBOR_1W, 'purple')

    streamlit_echarts.st_pyecharts(
        line_amt.overlap(line_irt).overlap(line_shibor_on).overlap(line_shibor_1w),
        # line_amt.overlap(line_irt),
        theme=ThemeType.WALDEN,
        height='500px'
    )

    st.divider()
    st.markdown("###  交易对手排名")
    st.markdown(" ")

    bar_party = bar_global(dh['partyn_total'], C.NAME,
                           '日均余额(亿元）', C.AVG_AMT, '加权利率（%）', C.WEIGHT_RATE)

    streamlit_echarts.st_pyecharts(
        bar_party,
        theme=ThemeType.WALDEN,
        height='800px',
    )

    st.divider()
    st.markdown("###  交易对手占比")
    st.markdown(" ")

    pie_party = pie_global(dh['party_n'], C.NAME, C.AVG_AMT, '日均余额(亿元）')

    streamlit_echarts.st_pyecharts(
        pie_party,
        theme=ThemeType.WALDEN,
        # height='800px',
        # width='50%'
    )

    with st.expander("交易对手明细(全量）"):
        # 把“合计”行放置到最后一行
        if dh['party_total'].empty is False:
            # 对输出格式化
            dh['party_total'] = FundDataHandler.format_output(dh['party_total'])

        st.dataframe(dh['party_total'][[C.NAME, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.NAME: '交易对手',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })

    st.divider()
    st.markdown("###  期限分析")
    st.write("###  ")

    # x_data = dh['term'][C.TERM_TYPE].values.tolist()
    # y_pie = (dh['term'][C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

    pie_term = pie_global(dh['term'], C.TERM_TYPE, C.AVG_AMT, '日均余额（亿元）')

    streamlit_echarts.st_pyecharts(
        pie_term,
        theme=ThemeType.WALDEN,
    )

    with st.expander("期限占比明细"):
        if dh['term_total'].empty is False:
            # 对输出格式化
            dh['term_total'] = FundDataHandler.format_output(dh['term_total'])

        st.dataframe(dh['term_total'][[C.TERM_TYPE, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]],
                     use_container_width=True,
                     column_config={
                         C.TERM_TYPE: '期限类别',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })
