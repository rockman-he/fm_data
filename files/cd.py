# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond
# Description: simple introduction of the code
from datetime import datetime

import streamlit as st

from bond_tx import CDTx
from utils.txn_factory import TxFactory
from utils.web_data import SecurityDataHandler
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from utils.web_view import pie_global, security_line

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="同业存单",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 同业存单")
st.divider()

txn = None
dh = None

# 按时间段查询的form
with st.form("CD"):
    txn_start_time, txn_end_time, txn_cps_type = st.columns([1, 1, 3])
    with txn_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=TimeUtil.get_current_and_last_year()[0],
            min_value=datetime(2013, 1, 1).date(),
            # 要明确每个组件的key，不然会共用一个组件
            key='cd_start_time'
        )

    with txn_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=TimeUtil.get_current_and_last_month_dates()[2],
            min_value=datetime(2013, 1, 1).date(),
            key='cd_end_time'
        )

    with txn_cps_type:
        pass

    txn_submit = st.form_submit_button('查  询')

if txn_submit:
    txn = TxFactory(CDTx).create_txn(start_time, end_time)
    dh = SecurityDataHandler(txn)

option = st.sidebar.selectbox(
    "选择统计类型",
    ("收益测算", "业务统计"),
    key='cd_option'
)

if option == '收益测算':

    if txn is not None and not dh.raw.empty:
        st.write("### 区间收益")
        st.markdown("###### ")

        daily_cum = dh.period_yield_all_cum(start_time, end_time)
        st.write(f"**日均存单持仓**: {daily_cum[C.HOLD_AMT].sum() / len(daily_cum):,.2f} 元")
        st.write(f"**日均资金占用**: {daily_cum[C.CAPITAL_OCCUPY].sum() / len(daily_cum):,.2f} 元")
        st.write(f"**利息收入**: {daily_cum[C.INST_A_DAY].sum():,.2f} 元")
        st.write(f"**净价浮盈**: {daily_cum.iloc[-1][C.NET_PROFIT_SUB]:,.2f} 元")
        st.write(f"**资本利得**: {daily_cum.iloc[-1][C.CAPITAL_GAINS_CUM]:,.2f} 元")
        st.write(f"**总收益**: {daily_cum.iloc[-1][C.TOTAL_PROFIT_CUM]:,.2f} 元")
        st.write(f"**区间收益率**: {daily_cum.iloc[-1][C.YIELD_CUM]:.4f}%")

        st.divider()

        streamlit_echarts.st_pyecharts(
            security_line(daily_cum),
            height='600px'
        )
        st.expander('详细数据').write(daily_cum)

        st.divider()

        st.markdown("### 单支存单收益")
        temple = {C.AVG_AMT: '日均持仓（元）',
                  C.CAPITAL_OCCUPY: '日均资金占用（元）',
                  C.INTEREST_AMT: '利息收入（元）',
                  C.NET_PROFIT_SUB: '净价浮盈（元）',
                  C.CAPITAL_GAINS: '资本利得（元）',
                  C.TOTAL_PROFIT_CUM: '总收益（元）',
                  C.YIELD_CUM: '区间收益率（%）'}
        st.dataframe(dh.yield_cum_by_code(start_time, end_time), use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.BOND_CODE: '存单代码',
                         C.BOND_NAME: '存单简称'
                     }, **temple})

        st.markdown("### 按发行人分类")
        st.dataframe(dh.yield_cum_by_org(start_time, end_time), use_container_width=True,
                     hide_index=True,
                     column_config={**{
                         C.ISSUE_ORG: '发行人'
                     }, **temple})

    else:
        st.write('无数据')

if option == '业务统计':
    if txn is not None and not dh.raw.empty:
        st.divider()
        st.write("### 持仓概览")
        holded_bonds = dh.get_holding_bonds_endtime()

        if not holded_bonds.empty:
            # 按发行人汇总
            holded_org = holded_bonds.groupby(C.ISSUE_ORG).agg({C.HOLD_AMT: 'sum'}).reset_index()
            st.write(
                f"截至{end_time}, **持仓面额**合计 {holded_bonds[C.HOLD_AMT].sum() / 100000000:,.2f} 亿元。 "
            )
            st.markdown("#### ")

            pie_bonds_org = pie_global(holded_org, C.ISSUE_ORG, C.HOLD_AMT, '按发行人分类')
            streamlit_echarts.st_pyecharts(pie_bonds_org, height='450px')

            output = holded_bonds.drop(columns=[C.DATE, C.BOND_TYPE, C.MARKET_CODE, C.BOND_TYPE_NUM]).style.format({
                C.HOLD_AMT: "{:,.2f}",
                C.COST_NET_PRICE: "{:.4f}",
                C.COST_FULL_PRICE: "{:.4f}",
                C.ISSUE_AMT: "{:,.2f}",
                C.ISSUE_PRICE: "{:.4f}",
                C.MATURITY: "{:%Y-%m-%d}",
                C.COUPON_RATE_ISSUE: "{:.2%}",
                C.COUPON_RATE_CURRENT: "{:.2%}"
            })

            st.divider()
            st.markdown("### 持仓存单基础信息")
            st.dataframe(output, use_container_width=True,
                         hide_index=True,
                         column_config={
                             C.BOND_CODE: '债券代码',
                             C.BOND_NAME: '债券简称',
                             C.HOLD_AMT: '持仓面额（元）',
                             C.COST_NET_PRICE: '成本净价',
                             C.COST_FULL_PRICE: '成本全价',
                             C.ISSUE_ORG: '发行人',
                             C.ISSUE_AMT: '发行量（元）',
                             C.ISSUE_PRICE: '发行价格',
                             C.COUPON_RATE_ISSUE: '票面利率（发行）',
                             C.COUPON_RATE_CURRENT: '票面利率（当期）',
                             C.MATURITY: '到期日'
                         })
        else:
            st.write("期末无持仓")

        st.divider()

        st.markdown("### 交易记录")
        all_trades = dh.get_all_trades()

        if not all_trades.empty:
            all_trades = all_trades.drop(columns=[C.MARKET_CODE]).style.format({
                C.DATE: "{:%Y-%m-%d}",
                C.NET_PRICE: "{:.4f}",
                C.FULL_PRICE: "{:.4f}",
                C.BOND_AMT_CASH: "{:,.2f}",
                C.ACCRUED_INST_CASH: "{:,.2f}",
                C.TRADE_AMT: "{:,.2f}",
                C.SETTLE_AMT: "{:,.2f}"
            })

            st.dataframe(all_trades, use_container_width=True, hide_index=True,
                         column_config={
                             C.DATE: '交易日期',
                             C.BOND_CODE: '存单代码',
                             C.BOND_NAME: '存单简称',
                             C.DIRECTION: '交易方向',
                             C.BOND_AMT_CASH: '交易面额（元）',
                             C.NET_PRICE: '交易净价',
                             C.ACCRUED_INST_CASH: '应计利息（元）',
                             C.TRADE_AMT: '交易金额（元）',
                             C.SETTLE_AMT: '结算金额（元）',
                             C.TRADE_TYPE: '交易类型',
                             C.FULL_PRICE: '交易全价'
                         })
        else:
            st.write("无交易记录")

    else:
        st.write("无数据")
