# Author: RockMan
# CreateTime: 2024/7/15
# FileName: 1_🏻_拆借业务.py
# Description: 用于展示拆借交易要素的页面
import pandas as pd
import streamlit as st
from pyecharts.options import LabelOpts

from transaction import IBO
from utils.display_util import DisplayUtil
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Pie
from pyecharts.globals import ThemeType

from utils.txn_factory import TxnFactory

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="拆借业务",
                   page_icon="🏻",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 拆借业务")
st.divider()

# 获取当前月和上个月的时间
# last_month_start = TimeUtil.get_current_and_last_month_dates()[1]
# last_month_end = TimeUtil.get_current_and_last_month_dates()[2]

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

txn_daily = pd.DataFrame({})
txn_party = pd.DataFrame({})
txn_party_total = pd.DataFrame({})
txn_party_n = pd.DataFrame({})
txn_term = pd.DataFrame({})
txn_term_total = pd.DataFrame({})
txn_partyn_total = pd.DataFrame({})
txn_occ = pd.DataFrame({})

if txn_submit:
    txn = TxnFactory(IBO).create_txn(start_time, end_time, cps_type)
    display = DisplayUtil(txn)

    txn_daily = display.daily_data()
    txn_party = display.party_rank()
    txn_party_total = display.add_total(txn_party, 1)
    txn_party_n = display.party_rank_n()
    txn_partyn_total = display.add_total(txn_party_n, 0)
    txn_term = display.term_rank()
    txn_term_total = display.add_total(txn_term, 1)
    txn_occ = display.occ_stats()
    # txn_partyn_total = DisplayUtil.add_total(txn_party_n, 0)

    # st.dataframe(txn_daily, use_container_width=True)

#
# if txn_submit:
#     txn = Repo(start_time, end_time, cps_type)
#     txn_daily = txn.daily_data(start_time, end_time, cps_type)
#     txn_party = txn.party_rank(start_time, end_time, cps_type)
#     txn_party_n = DisplayUtil.merge_lastn(txn_party)
#     txn_partyn_total = DisplayUtil.add_total(txn_party_n, 0)
#     txn_term = txn.term_type(start_time, end_time, cps_type)
#     txn_occ = txn.occ_stats(start_time, end_time, cps_type)

col1, col2, col3 = st.columns(3)
if txn_party.empty:
    st.write("无数据")
else:
    col1.metric("日均余额（亿元）", '{:,.2f}'.format(txn_partyn_total.loc[0, C.AVG_AMT] / 100000000))
    col2.metric("加权利率（%）", '{:.4f}'.format(txn_partyn_total.loc[0, C.WEIGHT_RATE]))
    col3.metric("加权天数", '{:.2f}'.format(txn_party_n[C.PRODUCT].sum() / txn_occ[C.TRADE_WEIGHT_SUM]))

    col1.metric("交易笔数", txn_occ[C.TRADE_NUM])
    col2.metric("最高加权利率（%）", '{:.2f}'.format(txn_daily[C.WEIGHT_RATE].max()))
    col3.metric("最高单笔利率（%）", '{:.2f}'.format(txn_occ[C.MAX_RATE] * 100))

    col1.metric("交易金额（亿元）", '{:,.2f}'.format(txn_occ[C.TRADE_SUM] / 100000000))
    col2.metric("最低加权利率（%）",
                '{:.2f}'.format(txn_daily.loc[txn_daily[C.WEIGHT_RATE] != 0, C.WEIGHT_RATE].min()))
    col3.metric("最低单笔利率（%）", '{:.2f}'.format(txn_occ[C.MIN_RATE] * 100))

st.divider()
st.markdown("#### 🥇 每日余额利率情况")
st.write("###  ")

if txn_daily.empty:
    st.write('无数据')
else:

    # 横坐标，时间序列
    x_pie = txn_daily[C.AS_DT].dt.strftime('%Y-%m-%d').values.tolist()

    line_amt = (
        Line()
        .add_xaxis(x_pie)
        # 主Y坐标轴（左边）
        .add_yaxis(
            # 图例显示
            "日均余额（亿元）",
            # 数据
            (txn_daily[C.TRADE_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(),
            # 定义bar柱体的颜色
            color="#37a2da",
            # 显示最高点的值
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
        )
        # 副Y坐标轴（右边）
        .extend_axis(
            yaxis=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),  # interval=5
            )
        )
        # 不显示每个bar的值
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        # 设置全局配置项
        .set_global_opts(
            # 以十字交叉坐标指针显示
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
        )
    )

    # 回购业务的加权利率曲线
    line_irt = (
        Line()
        .add_xaxis(x_pie)
        .add_yaxis(
            "加权利率（%）",
            txn_daily[C.WEIGHT_RATE].apply(lambda x: '%.2f' % x).values.tolist(),
            # 使用的 y 轴的 index，在单个图表实例中存在多个 y 轴的时候有用。
            # 因为使用的是副轴，所以为1（从0开始）
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            color='red',
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
        )
    )

    # 资金市场R001利率曲线
    line_shibor_on = (
        Line()
        .add_xaxis(x_pie)
        .add_yaxis(
            C.SHIBOR_ON,
            txn_daily[C.SHIBOR_ON].apply(lambda x: '%.2f' % x).values.tolist(),
            # 使用的 y 轴的 index，在单个图表实例中存在多个 y 轴的时候有用。
            # 因为使用的是副轴，所以为1（从0开始）
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            color='green',
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
        )
    )

    # 资金市场R007利率曲线
    line_shibor_1w = (
        Line()
        .add_xaxis(x_pie)
        .add_yaxis(
            C.SHIBOR_1W,
            txn_daily[C.SHIBOR_1W].apply(lambda x: '%.2f' % x).values.tolist(),
            # 使用的 y 轴的 index，在单个图表实例中存在多个 y 轴的时候有用。
            # 因为使用的是副轴，所以为1（从0开始）
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            color='purple',
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
        )
    )

    streamlit_echarts.st_pyecharts(
        line_amt.overlap(line_irt).overlap(line_shibor_on).overlap(line_shibor_1w),
        # line_amt.overlap(line_irt),
        theme=ThemeType.WALDEN,
        height='500px'
    )

st.divider()
st.markdown("#### 🚒 交易对手排名")
st.markdown(" ")

if txn_party.empty:
    st.write('无数据')
else:

    bar_party = (
        Bar()
        .add_xaxis(txn_partyn_total[C.NAME].values.tolist())
        .add_yaxis('日均余额(亿元）',
                   (txn_partyn_total[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(), )
        .add_yaxis(
            series_name='加权利率（%）',
            # 采用副坐标
            yaxis_index=1,
            y_axis=txn_partyn_total[C.WEIGHT_RATE].apply(lambda x: '%.2f' % x).values.tolist()
        )
        # .reversal_axis()
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="",
                type_="value",
                min_=0,
                max_='{:.2f}'.format(txn_daily[C.WEIGHT_RATE].max() * 2),
                interval=2,
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
            )
        )
        .set_series_opts(label_opts=opts.LabelOpts(position="top"))
        .set_global_opts(
            # 以十字交叉坐标指针显示
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)),
        )
    )

    streamlit_echarts.st_pyecharts(
        bar_party,
        theme=ThemeType.WALDEN,
        height='800px',
        # width='75%'
    )

st.divider()
st.markdown("#### ⛪ 交易对手占比")
st.markdown(" ")

if txn_party.empty:
    st.write('无数据')
else:

    x_pie = txn_party_n[C.NAME].values.tolist()
    y_pie = (txn_party_n[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

    pie_party = (
        Pie().add(
            series_name="日均余额",
            data_pair=[list(z) for z in zip(x_pie, y_pie)],
            radius=["70%", "90%"],
            # label_opts=opts.LabelOpts(is_show=True, position="outer"),
        )
        .set_global_opts(legend_opts=opts.LegendOpts(pos_left="legft", orient="vertical"))
        .set_series_opts(
            # tooltip_opts=opts.TooltipOpts(
            #     # trigger="item", formatter="{a} <br/>{b}: {c} 亿元 ({d}%)"
            #     formatter="{c} 亿元 ({d}%)"
            # ),
            label_opts=opts.LabelOpts(formatter="{c} 亿元 ({d}%)"),
        )
    )

    streamlit_echarts.st_pyecharts(
        pie_party,
        theme=ThemeType.WALDEN,
        # height='800px',
        # width='50%'
    )

    with st.expander("交易对手明细(全量）"):
        # 把“合计”行放置到最后一行
        if txn_party_total.empty is False:
            # 对输出格式化
            txn_party_total = DisplayUtil.format_output(txn_party_total)

        st.dataframe(txn_party_total[[C.NAME, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.NAME: '交易对手',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })

st.divider()
st.markdown("#### 🪟 期限分析")
st.write("###  ")

if txn_term.empty:
    st.write('无数据')
else:

    x_pie = txn_term[C.TERM_TYPE].values.tolist()
    y_pie = (txn_term[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

    pie_term = (
        Pie().add(
            series_name="日均余额：",
            data_pair=[list(z) for z in zip(x_pie, y_pie)],
            radius=["70%", "90%"],
        )
        .set_global_opts(legend_opts=opts.LegendOpts(pos_left="legft", orient="vertical"))
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{c} 亿元 ({d}%)"),
        )
    )

    streamlit_echarts.st_pyecharts(
        pie_term,
        theme=ThemeType.WALDEN,
    )

    with st.expander("期限占比明细"):
        if txn_term_total.empty is False:
            # 对输出格式化
            txn_term_total = DisplayUtil.format_output(txn_term_total)

        st.dataframe(txn_term_total[[C.TERM_TYPE, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.TERM_TYPE: '期限类别',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })
