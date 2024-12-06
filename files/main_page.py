# Author: RockMan
# CreateTime: 2024/10/30
# FileName: main_page
# Description: simple introduction of the code
import streamlit as st
import streamlit_echarts

from utils.web_data import OverviewDataHandler

from datetime import datetime
from utils.db_util import Constants as C
from utils.web_view import main_page_by_type, main_page_all_profit

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

    with st.spinner('生成底层业务数据...'):
        tx = OverviewDataHandler(year_num)

    with st.spinner('生成回购业务数据...'):
        repo = tx.fund_monthly_report_yoy(C.REPO, mark_rate, mark_rate)
        repl = tx.fund_monthly_report_yoy(C.REPL)

    with st.spinner('生成拆借业务数据...'):
        ibo = tx.fund_monthly_report_yoy(C.IBO, mark_rate, mark_rate)
        ibl = tx.fund_monthly_report_yoy(C.IBL)

    with st.spinner('生成债券业务数据...'):
        bond = tx.security_monthly_report_yoy(C.BOND)

    with st.spinner('生成存单业务数据...'):
        cd = tx.security_monthly_report_yoy(C.CD)

    df = tx.asset_debt_data()

    st.write("###  收入支出情况")
    st.write("####")

    streamlit_echarts.st_pyecharts(main_page_all_profit(df))

    st.dataframe(tx.get_tx_total(C.REPO, year_num))
    st.dataframe(tx.get_tx_total(C.REPL, year_num))
    st.dataframe(tx.get_tx_total(C.IBO, year_num))
    st.dataframe(tx.get_tx_total(C.IBL, year_num))

    st.write("###  各业务月度情况")


    # todo 补充回购及拆借业务的套息收入，业务明细
    @st.fragment
    def show_main_page():
        with st.container():
            tx_type = st.radio(" ", ["债券业务", "同业存单", "回购业务", "拆借业务"], index=0,
                               horizontal=True)

            if tx_type == "债券业务":
                streamlit_echarts.st_pyecharts(main_page_by_type(bond, '债券业务', '日均持仓（亿元）', C.AVG_AMT,
                                                                 '总收益（万元）', C.TOTAL_PROFIT, '加权收益率（%）',
                                                                 C.WEIGHT_RATE), height='500px')
            if tx_type == "回购业务":
                streamlit_echarts.st_pyecharts(main_page_by_type(repo, '正回购', '日均余额（亿元）', C.AVG_AMT,
                                                                 '利息支出（万元）', C.INST_DAYS, '加权利率（%）',
                                                                 C.WEIGHT_RATE), height='500px')

                streamlit_echarts.st_pyecharts(main_page_by_type(repl, '逆回购', '日均余额（亿元）', C.AVG_AMT,
                                                                 '利息收入（万元）', C.INST_DAYS, '加权利率（%）',
                                                                 C.WEIGHT_RATE), height='500px')

            if tx_type == '拆借业务':
                streamlit_echarts.st_pyecharts(main_page_by_type(ibo, '同业拆入', '日均余额（亿元）', C.AVG_AMT,
                                                                 '利息支出（万元）', C.INST_DAYS, '加权利率（%）',
                                                                 C.WEIGHT_RATE), height='500px')

                streamlit_echarts.st_pyecharts(main_page_by_type(ibl, '同业拆出', '日均余额（亿元）', C.AVG_AMT,
                                                                 '利息收入（万元）', C.INST_DAYS, '加权利率（%）',
                                                                 C.WEIGHT_RATE), height='500px')

            if tx_type == '同业存单':
                streamlit_echarts.st_pyecharts(main_page_by_type(cd, '同业存单', '日均持仓（亿元）', C.AVG_AMT,
                                                                 '总收益（万元）', C.TOTAL_PROFIT, '加权收益率（%）',
                                                                 C.WEIGHT_RATE), height='500px')


    show_main_page()

    st.dataframe(repo)
    st.dataframe(repl)
    st.dataframe(ibo)
    st.dataframe(ibl)
    st.dataframe(bond)
    st.dataframe(cd)
