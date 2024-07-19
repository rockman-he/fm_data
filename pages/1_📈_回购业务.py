# Author: RockMan
# CreateTime: 2024/7/15
# FileName: 1_📈_回购业务.py
# Description: 用于展示回购交易要素的页面
import pandas as pd
import streamlit as st
from pyecharts.options import LabelOpts

from transaction import Repo
from utils.display_util import DisplayUtil
from utils.market_util import MarketUtil
from utils.time_util import TimeUtil
from utils.db_util import Constants as C

import streamlit_echarts
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Pie
from pyecharts.globals import ThemeType

# set_page_config必须放在开头，不然会报错
st.set_page_config(page_title="回购业务",
                   page_icon="📈",
                   layout="wide",
                   # 左边sidebar默认是展开的
                   initial_sidebar_state="expanded")

st.markdown("## 🍳 回购业务")
st.divider()

# 获取当前月和上个月的时间
last_month_start = TimeUtil.get_current_and_last_month_dates()[1]
last_month_end = TimeUtil.get_current_and_last_month_dates()[2]

# 按时间段查询的form
with st.form("repo"):
    repo_start_time, repo_end_time, repo_cps_type = st.columns([1, 1, 3])
    with repo_start_time:
        start_time = st.date_input(
            "⏱起始时间",
            value=last_month_start,
            # 要明确每个组件的key，不然会共用一个组件
            key='repo_start_time'
        )

    with repo_end_time:
        end_time = st.date_input(
            "⏱结束时间",
            value=last_month_end,
            key='repo_end_time'
        )

    with repo_cps_type:
        cps_type = st.selectbox(
            '业务类型',
            ('正回购', '逆回购'),
            key='repo_cps_type'
        )

    repo_submit = st.form_submit_button('查  询')

market = MarketUtil()
repo_everyday = pd.DataFrame({})
repo_party = pd.DataFrame({})
repo_merge = pd.DataFrame({})
repo_term = pd.DataFrame({})

if repo_submit:
    repo = Repo(start_time, end_time, cps_type)
    # print(f"{start_time}{end_time}{cps_type}")
    repo_everyday = repo.daily_data(start_time, end_time, cps_type)
    repo_party = repo.party_rank(start_time, end_time, cps_type)
    repo_merge = DisplayUtil.merge_lastn(repo_party)
    repo_term = repo.term_type(start_time, end_time, cps_type)

st.divider()
st.markdown("#### 🥇 每日余额利率情况")
st.write("###  ")

if repo_everyday.empty:
    st.write('无数据')
else:

    # 关联资金市场利率
    market_irt = market.get_irt(start_time, end_time)
    repo_everyday = pd.merge(repo_everyday, market_irt, left_on=C.AS_DT, right_on=C.DATE, how='left')

    # 横坐标，时间序列
    x_pie = repo_everyday[C.AS_DT].dt.strftime('%Y-%m-%d').values.tolist()

    line_amt = (
        Line()
        .add_xaxis(x_pie)
        # 主Y坐标轴（左边）
        .add_yaxis(
            # 图例显示
            "日均余额（亿元）",
            # 数据
            (repo_everyday[C.REPO_AMOUNT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(),
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
            repo_everyday[C.WEIGHT_RATE].apply(lambda x: '%.2f' % x).values.tolist(),
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
    line_R001 = (
        Line()
        .add_xaxis(x_pie)
        .add_yaxis(
            "R001",
            repo_everyday[C.R001].apply(lambda x: '%.2f' % x).values.tolist(),
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
    line_R007 = (
        Line()
        .add_xaxis(x_pie)
        .add_yaxis(
            "R007",
            repo_everyday[C.R007].apply(lambda x: '%.2f' % x).values.tolist(),
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
        line_amt.overlap(line_irt).overlap(line_R001).overlap(line_R007),
        # line_amt.overlap(line_irt),
        theme=ThemeType.WALDEN,
        height='500px'
    )

st.divider()
st.markdown("#### 🚒 交易对手排名")
st.markdown(" ")

if repo_party.empty:
    st.write('无数据')
else:
    repo_rank = DisplayUtil.add_total(repo_merge, 0)

    bar_party = (
        Bar()
        .add_xaxis(repo_rank[C.MAIN_ORG].values.tolist())
        .add_yaxis('日均余额(亿元）', (repo_rank[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(), )
        .add_yaxis(
            series_name='加权利率（%）',
            # 采用副坐标
            yaxis_index=1,
            y_axis=repo_rank[C.WEIGHT_RATE].apply(lambda x: '%.2f' % x).values.tolist()
        )
        # .reversal_axis()
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="",
                type_="value",
                min_=0,
                max_='{:.2f}'.format(repo_everyday[C.WEIGHT_RATE].max() * 2),
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

if repo_party.empty:
    st.write('无数据')
else:

    x_pie = repo_merge[C.MAIN_ORG].values.tolist()
    y_pie = (repo_merge[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

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
        repo_all = DisplayUtil.add_total(repo_party)

        if repo_all.empty is False:
            # 对输出格式化

            repo_all = DisplayUtil.format_output(repo_all)

        st.dataframe(repo_all[[C.MAIN_ORG, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.MAIN_ORG: '交易对手',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })

st.divider()
st.markdown("#### 🪟 期限分析")
st.write("###  ")

if repo_term.empty:
    st.write('无数据')
else:

    x_pie = repo_term[C.TERM_TYPE].values.tolist()
    y_pie = (repo_term[C.AVG_AMT] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

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
        # 把“合计”行放置到最后一行
        repo_all = DisplayUtil.add_total(repo_term)

        if repo_all.empty is False:
            # 对输出格式化
            repo_all = DisplayUtil.format_output(repo_all)

        st.dataframe(repo_all[[C.TERM_TYPE, C.AVG_AMT, C.INST_GROUP, C.WEIGHT_RATE]], use_container_width=True,
                     column_config={
                         C.TERM_TYPE: '期限类别',
                         C.AVG_AMT: '日均余额（元）',
                         C.INST_GROUP: '利息支出',
                         C.WEIGHT_RATE: '加权利率（%）'
                     })
