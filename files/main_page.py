# Author: RockMan
# CreateTime: 2024/10/30
# FileName: main_page
# Description: simple introduction of the code
from datetime import timedelta

import pandas as pd
import streamlit as st

from bond_tx import CDTx, BondTx
from fund_tx import IBO, Repo
from utils.time_util import TimeUtil
from utils.txn_factory import TxFactory
from utils.web_data import FundDataHandler, SecurityDataHandler, fundtx_monthly_report, security_monthly_report
from utils.db_util import Constants as C
from datetime import datetime

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

        # if year_num == current_year:
        #     start_time = datetime(current_year, 1, 1).date()
        #     end_time = (datetime.now() - timedelta(days=1)).date()
        #
        #     if end_time < start_time:
        #         end_time = start_time
        #
        # else:
        #     start_time = datetime(year_num, 1, 1).date()
        #     end_time = datetime(year_num, 12, 31).date()

    # TODO 其实应该为存出利率，但是这里暂时用基准利率代替
    with txn_mark_rate:
        mark_rate = st.number_input(
            "基准利率（用于测算套息收入, %）",
            value=1.90,
            key='summary_mark_rate'
        )

    txn_submit = st.form_submit_button('查  询')

# txn = None
# dh = {'party': pd.DataFrame({})}

if txn_submit:
    st.write('同业拆入')
    df = fundtx_monthly_report(year_num, IBO, '同业拆入', mark_rate)
    st.dataframe(df)

    st.write('同业拆出')
    df = fundtx_monthly_report(year_num, IBO, '同业拆出')
    st.dataframe(df)

    st.write('正回购')
    df = fundtx_monthly_report(year_num, Repo, '正回购', mark_rate)
    st.dataframe(df)

    st.write('逆回购')
    df = fundtx_monthly_report(year_num, Repo, '逆回购')
    st.dataframe(df)

    st.write('同业存单')
    df = security_monthly_report(year_num, CDTx)
    st.dataframe(df)

    st.write('债券')
    df = security_monthly_report(year_num, BondTx)
    st.dataframe(df)

    # txn = CDTx(start_time, end_time)
    # cd = SecurityDataHandler(txn).get_summary(start_time, end_time)
    #
    # st.write('同业存单')
    # st.write(cd[C.AVG_AMT])
    # st.write(cd[C.INST_DAYS])
    # st.write(cd[C.CAPITAL_GAINS])
    # st.write(cd[C.WEIGHT_RATE])
    #
    # txn = BondTx(start_time, end_time)
    # bond = SecurityDataHandler(txn).get_summary(start_time, end_time)
    #
    # st.write('债券')
    # st.write(bond[C.AVG_AMT])
    # st.write(bond[C.INST_DAYS])
    # st.write(bond[C.CAPITAL_GAINS])
    # st.write(bond[C.WEIGHT_RATE])
