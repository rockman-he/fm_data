# Author: RockMan
# CreateTime: 2024/8/14
# FileName: web_view.py
# Description: simple introduction of the code
from typing import Dict

import pandas as pd
import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Pie
from pyecharts.charts.chart import RectChart
from pyecharts.options import LabelOpts
from pyecharts.globals import ThemeType

from utils.db_util import Constants as C


def fund_tx_header(datas: Dict) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("日均余额（亿元）", '{:,.2f}'.format(datas['partyn_total'].loc[0, C.AVG_AMT] / 100000000))
    col2.metric("加权利率（%）", '{:.4f}'.format(datas['partyn_total'].loc[0, C.WEIGHT_RATE]))
    col3.metric("加权天数", '{:.2f}'.format(datas['party_n'][C.PRODUCT].sum() / datas['occ'][C.TRADE_WEIGHT_SUM]))
    col1.metric("交易笔数", datas['occ'][C.TRADE_NUM])
    col2.metric("最高加权利率（%）", '{:.2f}'.format(datas['holded'][C.WEIGHT_RATE].max()))
    col3.metric("最高单笔利率（%）", '{:.2f}'.format(datas['occ'][C.MAX_RATE] * 100))
    col1.metric("交易金额（亿元）", '{:,.2f}'.format(datas['occ'][C.TRADE_SUM] / 100000000))
    col2.metric("最低加权利率（%）",
                '{:.2f}'.format(datas['holded'].loc[datas['holded'][C.WEIGHT_RATE] != 0, C.WEIGHT_RATE].min()))
    col3.metric("最低单笔利率（%）", '{:.2f}'.format(datas['occ'][C.MIN_RATE] * 100))


def fund_line_global(df: pd.DataFrame, xaxis: str, yaxis: str, yaxis_name: str, color: str = "#37a2da", title="",
                     subtitle="") -> Line:
    x_data = df[xaxis].dt.strftime('%Y-%m-%d').values.tolist()
    line = (
        Line()
        .add_xaxis(x_data)
        # 主Y坐标轴（左边）
        .add_yaxis(
            # 图例显示
            yaxis_name,
            # 数据
            (df[yaxis] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(),
            # 定义bar柱体的颜色
            color=color,
            # 显示最高点的值
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")],
                                              label_opts=(LabelOpts(font_size=9))),
            is_smooth=True
        )
        # 副Y坐标轴（右边）
        .extend_axis(
            yaxis=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
            )
        )
        # 不显示每个bar的值
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        # 设置全局配置项
        .set_global_opts(
            # 以十字交叉坐标指针显示
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross",
            ),
            title_opts=opts.TitleOpts(title=title, subtitle=subtitle),
        )
    )

    return line


def security_line(bond_data: pd.DataFrame) -> RectChart:
    daily_data_cum = bond_data

    line_global = (
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
        #            (daily_all_cum[C.CAPITAL_OCCUPY] / 100000000).apply(lambda x: round(x, 2)).values.tolist(),
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
            title_opts=opts.TitleOpts(title="收益分布", subtitle=""),
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
    line1 = line_component(daily_data_cum, C.DATE, C.YIELD_CUM, "区间收益率", color="#FF6347", yaxis_index=1)
    line2 = (
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

    return line_global.overlap(line1).overlap(line2)


def line_component(df: pd.DataFrame, xaxis: str, yaxis: str, yaxis_name: str, color: str = 'red',
                   yaxis_index=1) -> Line:
    x_data = df[xaxis].dt.strftime('%Y-%m-%d').values.tolist()

    line = (
        Line()
        .add_xaxis(x_data)
        .add_yaxis(
            yaxis_name,
            df[yaxis].apply(lambda x: '%.2f' % x).values.tolist(),
            # 使用的 y 轴的 index，在单个图表实例中存在多个 y 轴的时候有用。
            # 因为使用的是副轴，所以为1（从0开始）
            yaxis_index=yaxis_index,
            label_opts=opts.LabelOpts(is_show=False),
            color=color,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")],
                                              label_opts=(LabelOpts(font_size=9))),
            is_smooth=True
        )
    )

    return line


def bar_global(df: pd.DataFrame, xaxis: str, yaxis1_name: str, yaxis1: str, yaxis2_name: str, yaxis2: str) -> Bar:
    bar = (
        Bar()
        .add_xaxis(df[xaxis].values.tolist())
        .add_yaxis(yaxis1_name,
                   (df[yaxis1] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(), )
        .add_yaxis(
            series_name=yaxis2_name,
            # 采用副坐标
            yaxis_index=1,
            y_axis=df[yaxis2].apply(lambda x: '%.2f' % x).values.tolist()
        )
        # .reversal_axis()
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="",
                type_="value",
                min_=0,
                max_='{:.2f}'.format(df[yaxis2].max() * 2),
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

    return bar


def pie_global(df: pd.DataFrame, xaxis: str, yaxis: str, title: str):
    x_data = df[xaxis].values.tolist()
    y_data = (df[yaxis] / 100000000).apply(lambda x: '%.2f' % x).values.tolist()

    pie = (
        Pie().add(
            series_name=title,
            data_pair=[list(z) for z in zip(x_data, y_data)],
            radius=["70%", "90%"],
        )
        .set_global_opts(legend_opts=opts.LegendOpts(pos_left="legft", orient="vertical"))
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{c} 亿元 ({d}%)"),
        )
    )
    return pie
