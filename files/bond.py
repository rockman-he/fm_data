# Author: RockMan
# CreateTime: 2024/8/15
# FileName: cd
# Description: simple introduction of the code
import numpy as np
import pandas as pd
import streamlit as st
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
from utils.web_view import tx_header, line_global, line_component, bar_global, pie_global
from pyecharts.charts import Grid, Bar, Line
from pyecharts import options as opts

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="债券业务",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 债券业务")
st.divider()

txn = None
daily_data = pd.DataFrame({})
daily_data_inst = pd.DataFrame({})
daily_data_credit = pd.DataFrame({})

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
    daily_data = dh.daily_yield_all().reset_index()
    daily_data_inst = dh.daily_yield_inst_rate_bond().reset_index()
    daily_data_credit = dh.daily_yield_credit_bond().reset_index()

bond_code = '160017.IB'

if txn is not None:

    if not daily_data.empty:
        st.divider()
        # st.write("#### 每日持仓和收益率")
        # st.write("###  ")

        # 创建一个包含从start_time到end_time的所有日期的新的DataFrame
        date_range = pd.date_range(start=start_time, end=end_time)
        df_null = pd.DataFrame(date_range, columns=[C.DATE])

        # st.dataframe(daily_data)

        # 扩充daily_data，使其包含所有的日期
        daily_data_all = pd.merge(df_null, daily_data, on=C.DATE, how='left')
        # 使用fillna函数将所有的缺失值填充为0
        daily_data_all = daily_data_all.fillna(0)

        # 日均余额曲线
        line_amt_all = line_global(daily_data_all, C.DATE, C.HOLD_AMT, "每日持仓（亿元）", title="所有债券")
        # 收益率
        line_yield_all = line_component(daily_data_all, C.DATE, C.YIELD, "收益率（%）", color="#FF6347")
        # 收益率不包含净价浮盈
        line_yield_nn_all = line_component(daily_data_all, C.DATE, C.YIELD_NO_NET_PROFIT, "收益率（EN,%）", color="green")

        daily_data_inst = pd.merge(df_null, daily_data_inst, on=C.DATE, how='left')
        daily_data_inst = daily_data_inst.fillna(0)

        line_amt_inst = line_global(daily_data_inst, C.DATE, C.HOLD_AMT, "每日持仓（亿元）", title="利率债")
        line_yield_inst = line_component(daily_data_inst, C.DATE, C.YIELD, "收益率（%）", color="#FF6347")
        line_yield_nn_inst = line_component(daily_data_inst, C.DATE, C.YIELD_NO_NET_PROFIT, "收益率（EN,%）",
                                            color="green")

        line_amt_credit = line_global(daily_data_credit, C.DATE, C.HOLD_AMT, "每日持仓（亿元）", title="信用债")
        line_yield_credit = line_component(daily_data_credit, C.DATE, C.YIELD, "收益率（%）", color="#FF6347")
        line_yield_nn_credit = line_component(daily_data_credit, C.DATE, C.YIELD_NO_NET_PROFIT, "收益率（EN,%）",
                                              color="green")

        # tab_all, tab_inst, tab_credit = st.columns(3)
        #
        # with tab_all:
        #     streamlit_echarts.st_pyecharts(
        #         line_amt_all.overlap(line_yield_all.overlap(line_yield_nn_all)),
        #         theme=ThemeType.WALDEN,
        #         height='450px'
        #     )
        #
        #     st.expander('详细数据').write(daily_data_all)
        #
        # with tab_inst:
        #     # st.write('test')
        #     streamlit_echarts.st_pyecharts(
        #         line_amt_inst.overlap(line_yield_inst.overlap(line_yield_nn_inst)),
        #         theme=ThemeType.WALDEN,
        #         height='450px'
        #
        #     )
        #     st.expander('详细数据').write(daily_data_inst)
        #
        # with tab_credit:
        #     streamlit_echarts.st_pyecharts(
        #         line_amt_credit.overlap(line_yield_credit.overlap(line_yield_nn_credit)),
        #         theme=ThemeType.WALDEN,
        #         height='450px'
        #     )
        #
        #     st.expander('详细数据').write(daily_data_credit)

        # st.divider()

        st.write("#### 区间收益")
        st.write("###  ")

        daily_data_cum = pd.merge(df_null, daily_data, on=C.DATE, how='left')
        # 创建一个标志列，用于标记何时开始新的累加
        # daily_data_cum['flag'] = daily_data_cum[C.INST_A_DAY].isna().astype(int).cumsum()
        daily_data_cum[C.INST_A_DAY] = daily_data_cum[C.INST_A_DAY].fillna(0)
        daily_data_cum[C.INST_DAYS] = daily_data_cum[C.INST_A_DAY].cumsum()

        daily_data_cum[C.CAPITAL_GAINS] = daily_data_cum[C.CAPITAL_GAINS].fillna(0)
        daily_data_cum[C.CAPITAL_GAINS_CUM] = daily_data_cum[C.CAPITAL_GAINS].cumsum()

        daily_data_cum[C.NET_PROFIT] = daily_data_cum[C.NET_PROFIT].fillna(0)
        daily_data_cum[C.NET_PROFIT_SUB] = daily_data_cum[C.NET_PROFIT] - daily_data_cum[C.NET_PROFIT].iloc[0]
        # 如果当日无持仓，忽略当日的净价浮盈
        daily_data_cum[C.HOLD_AMT] = daily_data_cum[C.HOLD_AMT].fillna(0)
        # daily_data_cum.loc[daily_data_cum[C.HOLD_AMT] == 0, C.NET_PROFIT_SUB] = 0
        daily_data_cum.loc[daily_data_cum[C.HOLD_AMT] == 0, C.NET_PROFIT_SUB] = 0

        daily_data_cum[C.TOTAL_PROFIT_CUM] = daily_data_cum[C.NET_PROFIT_SUB] + daily_data_cum[C.CAPITAL_GAINS_CUM] + \
                                             daily_data_cum[C.INST_DAYS]

        #  对daily_data_cum增加一列C.YIELD，其值为daily_data_cum[C.TOTAL_PROFIT_CUM]除以当前行及以前非空的daily_data_cum[C.CAPITAL_OCCUPY]的和
        # 计算daily_data_cum[C.CAPITAL_OCCUPY]的累积和
        daily_data_cum[C.CAPITAL_OCCUPY] = daily_data_cum[C.CAPITAL_OCCUPY].fillna(0)
        daily_data_cum['cumulative_capital_occupy'] = daily_data_cum[C.CAPITAL_OCCUPY].cumsum()

        # 将C.CAPITAL_OCCUPY列中的非零值设置为1
        daily_data_cum['non_zero'] = (daily_data_cum[C.CAPITAL_OCCUPY] != 0).astype(int)

        # 计算累积和
        daily_data_cum['days'] = daily_data_cum['non_zero'].cumsum()

        # 删除临时列
        # del daily_data_cum['non_zero']

        # daily_data_cum[C.INST_DAYS] * 365 / daily_data_cum['days'] + daily_data_cum[C.CAPITAL_GAINS_CUM] + \
        # daily_data_cum[C.NET_PROFIT_SUB]

        # 计算C.YIELD列的值
        daily_data_cum[C.YIELD_CUM] = ((daily_data_cum[C.INST_DAYS] * 365 /
                                        daily_data_cum['days'] + daily_data_cum[C.CAPITAL_GAINS_CUM] +
                                        daily_data_cum[C.NET_PROFIT_SUB]) /
                                       (daily_data_cum['cumulative_capital_occupy'] /
                                        daily_data_cum['days']) * 100)

        # # 为了避免除以0的情况，我们可以将结果中的NaN和inf值替换为0
        # daily_data_cum[C.YIELD].replace([np.inf, -np.inf, np.nan], 0, inplace=True)

        # st.dataframe(daily_data_cum)

        c = (
            Line()
            .add_xaxis(daily_data_cum[C.DATE].dt.strftime('%Y-%m-%d').values.tolist())
            .add_yaxis("总收益",
                       (daily_data_cum[C.TOTAL_PROFIT_CUM] / 10000).apply(lambda x: round(x, 2)).values.tolist(),
                       is_smooth=True, color="darkseagreen", yaxis_index=2)
            .add_yaxis("利息收入", (daily_data_cum[C.INST_DAYS] / 10000).apply(lambda x: round(x, 2)).values.tolist(),
                       is_smooth=True, color="#6495ED", yaxis_index=2)
            .add_yaxis("资本利得",
                       (daily_data_cum[C.CAPITAL_GAINS_CUM] / 10000).apply(lambda x: round(x, 2)).values.tolist(),
                       is_smooth=True, color="#EEB422", yaxis_index=2)
            .add_yaxis("净价浮盈",
                       (daily_data_cum[C.NET_PROFIT_SUB] / 10000).apply(lambda x: round(x, 2)).values.tolist(),
                       is_smooth=True, color="lightslategray", yaxis_index=2)
            # .add_yaxis("资金占用",
            #            (daily_data_cum[C.CAPITAL_OCCUPY] / 100000000).apply(lambda x: round(x, 2)).values.tolist(),
            #            yaxis_index=0, is_smooth=True, color="green")
            .set_series_opts(
                areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
                label_opts=opts.LabelOpts(is_show=False),
            )
            .extend_axis(
                yaxis=opts.AxisOpts(
                    name='收益率(%)',
                    position="left",
                    axislabel_opts=opts.LabelOpts(formatter="{value}"),
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="#FF6347")
                    ),
                )
            )
            .extend_axis(
                yaxis=opts.AxisOpts(
                    name='收益(万元)',
                    position="right",
                    axislabel_opts=opts.LabelOpts(formatter="{value}"),
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="darkseagreen")
                    ),
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="收益分布", subtitle="所有债券"),
                xaxis_opts=opts.AxisOpts(
                    axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
                    is_scale=False,
                    boundary_gap=False,
                ),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    name="资金占用（亿元）",
                    position="right",
                    offset=100,
                    axislabel_opts=opts.LabelOpts(formatter="{value}"),
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="darkslategray")
                    ),
                ),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True, trigger="axis", axis_pointer_type="cross",
                ),
            )
        )

        c2 = line_component(daily_data_cum, C.DATE, C.YIELD_CUM, "区间收益率", color="#FF6347", yaxis_index=1)
        # .add_yaxis("资金占用",
        #            (daily_data_cum[C.CAPITAL_OCCUPY] / 100000000).apply(lambda x: round(x, 2)).values.tolist(),
        #            yaxis_index=0, is_smooth=True, color="green")

        # c2.set_series_opts(label_opts=opts.LabelOpts(is_show=True))

        c3 = (
            Line()
            .add_xaxis(daily_data_cum[C.DATE].dt.strftime('%Y-%m-%d').values.tolist())
            .add_yaxis(
                series_name="资金占用",
                y_axis=(daily_data_cum[C.CAPITAL_OCCUPY] / 100000000).apply(lambda x: round(x, 2)).values.tolist(),
                yaxis_index=0,
                label_opts=opts.LabelOpts(is_show=False),
                color='darkslategray',
                markpoint_opts=opts.MarkPointOpts(
                    data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")],
                    label_opts=(LabelOpts(font_size=9))),
                is_smooth=True
            )
        )

        streamlit_echarts.st_pyecharts(
            c.overlap(c2).overlap(c3),
            # c,
            theme=ThemeType.WALDEN,
            height='700px'
        )

        st.expander('详细数据').write(daily_data_cum.loc[daily_data_cum[C.HOLD_AMT] != 0, :])

else:
    st.divider()
