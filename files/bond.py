# Author: RockMan
# CreateTime: 2024/8/15
# FileName: cd
# Description: simple introduction of the code

import streamlit as st
from bond_tx import BondTx
from utils.web_data import SecurityDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C
import streamlit_echarts
from utils.web_view import security_line, pie_global

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

# Using object notation
option = st.sidebar.selectbox(
    "选择统计类型",
    ("收益测算", "业务统计"),
    key='bond_option'
)

if option == '收益测算':

    if txn is not None and not dh.get_raw().empty:

        st.write("#### 区间收益")
        st.write("###  ")

        daily_all_cum = dh.period_yield_all_cum(start_time, end_time)
        daily_all_cum[C.BOND_TYPE] = '全部债券'
        daily_inst_cum = dh.period_yield_inst_cum(start_time, end_time)
        daily_inst_cum[C.BOND_TYPE] = '利率债'
        daily_credit_cum = dh.period_yield_credit_cum(start_time, end_time)
        daily_credit_cum[C.BOND_TYPE] = '信用债'


        @st.fragment
        def yield_chart():
            with st.container():
                bond_type = st.radio("### 债券类型", ['全部债券', '利率债', '信用债'], index=0, horizontal=True)
                if bond_type == '全部债券':
                    streamlit_echarts.st_pyecharts(
                        security_line(daily_all_cum),
                        height='600px'
                    )

                    # st.dataframe(SecurityDataHandler.bond_yield_format(daily_all_cum))
                    st.expander('详细数据').write(daily_all_cum)

                if bond_type == '利率债':
                    streamlit_echarts.st_pyecharts(
                        security_line(daily_inst_cum),
                        height='600px'
                    )

                    st.expander('详细数据').write(daily_inst_cum)

                if bond_type == '信用债':
                    streamlit_echarts.st_pyecharts(
                        security_line(daily_credit_cum),
                        height='600px'
                    )

                    st.expander('详细数据').write(daily_credit_cum)


        # 区间收益图表
        yield_chart()
        st.divider()

        temple = {C.AVG_AMT: '日均债券持仓（元）',
                  C.CAPITAL_OCCUPY: '日均资金占用（元）',
                  C.INTEREST_AMT: '利息收入（元）',
                  C.NET_PROFIT_SUB: '净价浮盈（元）',
                  C.CAPITAL_GAINS: '资本利得（元）',
                  C.TOTAL_PROFIT_CUM: '总收益（元）',
                  C.YIELD_CUM: '区间收益率（%）'}

        st.markdown("#### 单支债券收益")
        st.dataframe(dh.yield_cum_by_code(start_time, end_time), use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.BOND_CODE: '债券代码',
                         C.BOND_NAME: '债券名称'
                     }, **temple})
        st.divider()

        st.markdown("#### 按债券类型分类")
        st.dataframe(SecurityDataHandler.yield_data_format([daily_inst_cum, daily_credit_cum,
                                                            daily_all_cum], start_time, end_time, [C.BOND_TYPE]),
                     use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.BOND_TYPE: '债券类型'
                     }, **temple})
        st.divider()

        st.markdown("#### 按交易市场分类")
        st.dataframe(dh.yield_cum_by_market(start_time, end_time), use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.MARKET_CODE: '市场代码'
                     }, **temple})
        st.divider()

        st.markdown("#### 按发行人分类")
        st.dataframe(dh.yield_cum_by_org(start_time, end_time), use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.ISSUE_ORG: '发行人'
                     }, **temple})

    else:
        st.divider()

if option == '业务统计':
    if txn is not None and not dh.get_raw().empty:
        st.write("#### 债券持仓(" + str(end_time) + ")")
        holded_bonds = dh.get_holded_bonds_endtime()

        holded_bonds.loc[holded_bonds[C.BOND_TYPE_NUM].isin(C.INST_BOND_NUM), C.BOND_CUST] = '利率债'
        holded_bonds.loc[~holded_bonds[C.BOND_TYPE_NUM].isin(C.INST_BOND_NUM), C.BOND_CUST] = '信用债'

        # 按发行人汇总
        holded_org = holded_bonds.groupby(C.ISSUE_ORG).agg({C.HOLD_AMT: 'sum'}).reset_index()
        # 按债券类型汇总
        holded_type = holded_bonds.groupby(C.BOND_TYPE).agg({C.HOLD_AMT: 'sum'}).reset_index()
        # 按交易市场分类
        holded_market = holded_bonds.groupby(C.MARKET_CODE).agg({C.HOLD_AMT: 'sum'}).reset_index()
        # 按托管市场分类
        holded_cust = holded_bonds.groupby(C.BOND_CUST).agg({C.HOLD_AMT: 'sum'}).reset_index()

        pie_bonds_org = pie_global(holded_org, C.ISSUE_ORG, C.HOLD_AMT, '按发行人分类')
        pie_bonds_type = pie_global(holded_type, C.BOND_TYPE, C.HOLD_AMT, '按债券类型分类')
        pie_bonds_market = pie_global(holded_market, C.MARKET_CODE, C.HOLD_AMT, '按交易市场分类')
        pie_bonds_cust = pie_global(holded_cust, C.BOND_CUST, C.HOLD_AMT, '按托管市场分类')

        x_one, x_two = st.columns([1, 1])
        with x_one:
            streamlit_echarts.st_pyecharts(pie_bonds_cust, height='250px')
        with x_two:
            streamlit_echarts.st_pyecharts(pie_bonds_org, height='250px')

        y_one, y_two = st.columns([1, 1])
        with y_one:
            streamlit_echarts.st_pyecharts(pie_bonds_type, height='250px')
        with y_two:
            streamlit_echarts.st_pyecharts(pie_bonds_market, height='250px')

        output = holded_bonds.drop(columns=[C.DATE, C.BOND_TYPE_NUM]).style.format({
            C.HOLD_AMT: "{:,.2f}",
            C.COST_NET_PRICE: "{:.4f}",
            C.COST_FULL_PRICE: "{:.4f}",
            C.ISSUE_AMT: "{:,.2f}",
            C.ISSUE_PRICE: "{:.4f}",
            C.MATURITY: "{:%Y-%m-%d}",
            C.COUPON_RATE_ISSUE: "{:.2%}",
            C.COUPON_RATE_CURRENT: "{:.2%}"
        })

        st.dataframe(output, use_container_width=True,
                     hide_index=True,
                     column_config={
                         C.BOND_CODE: '债券代码',
                         C.BOND_NAME: '债券名称',
                         C.BOND_CUST: '托管市场',
                         C.MARKET_CODE: '交易市场',
                         C.HOLD_AMT: '持仓金额（元）',
                         C.COST_NET_PRICE: '成本净价',
                         C.COST_FULL_PRICE: '成本全价',
                         C.BOND_TYPE: '债券类型',
                         C.ISSUE_ORG: '发行人',
                         C.ISSUE_AMT: '发行量',
                         C.ISSUE_PRICE: '发行价格',
                         C.COUPON_RATE_ISSUE: '票面利率（发行）',
                         C.COUPON_RATE_CURRENT: '票面利率（当期）',
                         C.MATURITY: '到期日'
                     })
        # st.dataframe(txn.get_holded_bonds())
