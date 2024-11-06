# Author: RockMan
# CreateTime: 2024/10/30
# FileName: main_page
# Description: simple introduction of the code
import pandas as pd
import streamlit as st
import streamlit_echarts
from pyecharts.globals import ThemeType
from pyecharts.options import LabelOpts

from bond_tx import CDTx, BondTx
from fund_tx import IBO, Repo
from utils.web_data import fundtx_monthly_report, security_monthly_report, fundtx_monthly_report_yoy

from datetime import datetime
from pyecharts.charts import Line, Bar, Pie
from utils.db_util import Constants as C

import pyecharts.options as opts
from pyecharts.charts import Bar, Line

from utils.web_view import main_fundtx_chart

st.set_page_config(page_title="业务总览",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 业务总览")
st.divider()

# 按时间段查询的form
with st.form("summary"):
    txn_year, txn_mark_rate, place_holder = st.columns([1, 1, 1])

    with txn_year:
        current_year = datetime.now().year
        year_num = st.number_input("请选择年份",
                                   max_value=current_year,
                                   min_value=2013,
                                   value=current_year)

    # TODO 其实应该为存出利率，但是这里暂时用基准利率代替
    with txn_mark_rate:
        mark_rate = st.number_input(
            "基准利率（用于测算套息收入, %）",
            value=1.90,
            key='summary_mark_rate'
        )

    txn_submit = st.form_submit_button('查  询')

if txn_submit:
    st.write('同业拆入')

    merged = fundtx_monthly_report_yoy(year_num, IBO, '同业拆入', mark_rate, mark_rate)

    cols = [col for col in merged.columns if '_P' not in col]

    st.dataframe(merged.loc[:, cols])

    # streamlit_echarts.st_pyecharts(main_fundtx_chart(current, '日均余额（亿元）', '利息支出（万元）', '加权利率（%）'),
    #                                theme=ThemeType.WALDEN,
    #                                height='500px')
    #
    # streamlit_echarts.st_pyecharts(main_fundtx_chart(previous, '日均余额（亿元）', '利息支出（万元）', '加权利率（%）'),
    #                                theme=ThemeType.WALDEN,
    #                                height='500px')

    # st.write('同业拆出')
    # current = fundtx_monthly_report(year_num, IBO, '同业拆出')
    # st.dataframe(current)
    #
    # st.write('正回购')
    # current = fundtx_monthly_report(year_num, Repo, '正回购', mark_rate)
    # st.dataframe(current)
    #
    # st.write('逆回购')
    # current = fundtx_monthly_report(year_num, Repo, '逆回购')
    # st.dataframe(current)
    #
    # st.write('同业存单')
    # current = security_monthly_report(year_num, CDTx)
    # st.dataframe(current)
    #
    # st.write('债券')
    # current = security_monthly_report(year_num, BondTx)
    # st.dataframe(current)
