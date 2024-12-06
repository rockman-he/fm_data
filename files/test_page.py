# Author: RockMan
# CreateTime: 2024/8/15
# FileName: bond
# Description: simple introduction of the code

import streamlit as st

from bond_tx import SecurityTx
from utils.time_util import TimeUtil
from utils.txn_factory import TxFactory
from utils.web_data import SecurityDataHandler

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="数据测试",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 数据测试")
st.divider()

txn = None
security = None

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

    bond_code = st.text_input("请输入债券代码", '160017.IB')

    txn_submit = st.form_submit_button('查  询')

if txn_submit:
    # txn = SecurityTx(start_time, end_time)
    txn = TxFactory(SecurityTx).create_txn(start_time, end_time)
    security = SecurityDataHandler(txn)

# bond_code = '112303195.IB'

if txn is not None:
    st.write('## 债券业务')
    st.divider()

    st.write('### 债券持仓记录')
    st.write('#### 区间+前后7天，持仓的所有债券的基础信息, _holded_bonds_info_expand，不包括收益凭证')
    st.dataframe(txn.holded_bonds_info)

    st.write('### 时点末持仓债券基础信息')
    st.dataframe(security.get_holding_bonds_endtime(), use_container_width=True)

    st.write('#### 区间内持仓债券明细, _daily_holded_all()')
    st.dataframe(txn.holded)
    # #
    st.write('#### ' + bond_code + '的每日持仓, daily_holded_bond(bond_code)')
    st.dataframe(txn.daily_holded_bond(bond_code))
    st.divider()

    st.write('### 利息计算')
    st.write('#### 区间内所有持仓债券利息现金流, inst_flow_all()')
    st.dataframe(txn.insts_flow_all)
    #
    st.write('#### ' + bond_code + '的利息现金流, get_inst_flow(bond_code)')
    st.dataframe(txn.get_inst_flow(bond_code))

    st.write('#### ' + bond_code + '每日利息, get_daily_insts(bond_code)')
    st.dataframe(txn.get_daily_insts(bond_code), use_container_width=True)
    st.divider()

    st.write('### 净价浮盈')
    st.write('#### 区间内持仓债券估值get_daily_value_all()，若数据库内缺少估值，则在daily_value(bond_code)置为100')
    st.dataframe(txn.value)

    st.write('#### ' + bond_code + '的估值, get_daily_value(bond_code)')
    st.dataframe(txn.get_daily_value(bond_code))

    st.write('#### 每日净价浮盈, get_daily_net_profit(bond_code)')
    df7 = txn.get_daily_net_profit(bond_code)
    st.dataframe(df7, use_container_width=True)
    st.divider()

    st.write('### 资本利得')
    st.write('#### 交易记录')
    st.write('#### 一级申购，request_distributions()')
    st.dataframe(txn.primary_trades)

    st.write('#### 二级交易, get_all_trades()')
    st.dataframe(txn.secondary_trades)

    st.write('#### 资本利得, get_capital_all()')
    st.dataframe(txn.capital, use_container_width=True)

    st.write('#### ' + bond_code + ' 资本利得, get_capital_gains(bond_code)')
    st.dataframe(txn.get_capital_gains(bond_code), use_container_width=True)
    st.divider()

    st.write('### 综合收益汇总')
    st.write('#### ' + bond_code + '的综合收益, sum_profits(bond_code)')
    st.dataframe(txn.sum_profits(bond_code), use_container_width=True)

    st.write('#### 所有债券的综合收益, get_all_profit_data()')
    st.dataframe(txn.get_all_daily_profit(), use_container_width=True)

    d = SecurityDataHandler(txn)

    st.write('#### 每日收益合计, daily_yield_all()')
    st.dataframe(d.daily_yield_all(), use_container_width=True)

    st.write('#### 所有债券的总收益yield_all_cum_by_code(start_time, end_time)')
    st.dataframe(d.yield_cum_by_code(start_time, end_time), use_container_width=True)
