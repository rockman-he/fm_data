# Author: RockMan
# CreateTime: 2024/10/30
# FileName: main_page
# Description: simple introduction of the code


import streamlit as st
import streamlit_echarts
from pyecharts.globals import ThemeType

from bond_tx import CDTx, BondTx
from fund_tx import IBO, Repo
from utils.web_data import fundtx_monthly_report, security_monthly_report

from datetime import datetime
from pyecharts.charts import Line, Bar, Pie
from utils.db_util import Constants as C

from utils.web_view import fund_line_global, line_component, bar_global
import pyecharts.options as opts
from pyecharts.charts import Bar, Line

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
    df = fundtx_monthly_report(year_num, IBO, '同业拆入', mark_rate)
    st.dataframe(df)

    df = df.reset_index()

    bar = (
        Bar()
        .add_xaxis(df[C.DATE].dt.strftime('%Y-%m-%d').values.tolist())
        .add_yaxis(series_name='日均余额（亿元）',
                   # 相同组间的柱体间距
                   gap=0,
                   # 不同组间的柱体间距
                   category_gap="50%",
                   y_axis=(df[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(),
                   # 控制透明度
                   itemstyle_opts=opts.ItemStyleOpts(color="rgba(16, 78, 139, 0.8)"))
        .add_yaxis(series_name='利息收入/支出（万元）',
                   y_axis=(df[C.INST_DAYS] / 10000).apply(lambda x: '%.2f' % x).values.tolist(),
                   yaxis_index=1,
                   gap=0,
                   category_gap="50%",
                   itemstyle_opts=opts.ItemStyleOpts(color="rgba(238, 173, 14, 0.8)"))
        .extend_axis(
            yaxis=opts.AxisOpts(
                name='',
                position="right",
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
                max_='{:.2f}'.format(df[C.INST_DAYS].max() / 10000 * 3),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#eead0e")
                ),
                # 去掉该坐标系的间隔线
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="",
                type_="value",
                min_=0,
                max_='{:.2f}'.format(df[C.WEIGHT_RATE].max() * 1.2),
                interval=2,
                # 和其他y坐标轴的间距
                offset=70,
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="red")
                ),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            )
        )
        .set_series_opts(areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
                         # bar_category_gap="90%",
                         label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(

            # 以十字交叉坐标指针显示
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)),
            yaxis_opts=opts.AxisOpts(
                max_='{:.2f}'.format(df[C.AVG_AMT].max() / 100000000 * 1.3),
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#eead0e")
                )
            )
        )
    )

    line = (
        Line()
        .add_xaxis(xaxis_data=df[C.DATE].dt.strftime('%Y-%m-%d').values.tolist())
        .add_yaxis(
            series_name="加权利率（%）",
            yaxis_index=2,
            y_axis=df[C.WEIGHT_RATE].apply(lambda x: '%.2f' % x).values.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
            color='red',
            is_smooth=True
        )
    )

    streamlit_echarts.st_pyecharts(bar.overlap(line),
                                   theme=ThemeType.WALDEN,
                                   height='500px')

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
