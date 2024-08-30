from st_aggrid import AgGrid
import pandas as pd

import streamlit as st

from bond_tx import SecurityTx
from utils.time_util import TimeUtil
from pyecharts.charts import Line, Bar, Pie

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
    txn = SecurityTx(start_time, end_time)

bond_code = '160017.IB'


@st.fragment
def fragment_df(txn: SecurityTx) -> AgGrid:
    df = txn.get_holded_bonds_info()
    grid_return = AgGrid(df)
    return grid_return


if txn is not None:
    st.write('## 债券业务')
    st.divider()

    st.write('### 债券持仓记录')
    st.write('#### 所有债券的基础信息, get_holded_bonds_info()，不包括收益凭证')
    st.dataframe(txn.get_holded_bonds_info())

    fragment_df(txn)

    st.write('ok')
