# Author: RockMan
# CreateTime: 2024/7/15
# FileName: 1_📈_回购业务.py
# Description: 用于展示回购交易要素的页面
import pandas as pd
import streamlit as st
from pyecharts.options import LabelOpts

from transaction import Repo
from utils.market_util import MarketUtil
from utils.time_util import TimeUtil
from utils.database_util import Constants as C

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

# 初始化Repo类
repo = Repo()
market = MarketUtil()
repo_everyday = pd.DataFrame({})

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

if repo_submit:
    repo_everyday = repo.repo_everyday(start_time, end_time, cps_type)

st.divider()

st.markdown("#### 🥇 每日余额利率情况")
st.write("###  ")

if repo_everyday.empty:
    st.write('无数据')
else:

    # 关联资金市场利率
    # TODO 重构，1. 引入一个专门用于控制界面控件交互的中间类(Mediator)来降低界面控件之间的耦合度。2. 用tranaction接口来获取数据
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
