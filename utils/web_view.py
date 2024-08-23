# Author: RockMan
# CreateTime: 2024/8/14
# FileName: web_view.py
# Description: simple introduction of the code
from typing import Dict

import pandas as pd
import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Pie
from pyecharts.options import LabelOpts

from utils.db_util import Constants as C


def tx_header(datas: Dict) -> None:
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


def line_global(df: pd.DataFrame, xaxis: str, yaxis: str, title: str, color: str = "#37a2da") -> Line:
    x_data = df[xaxis].dt.strftime('%Y-%m-%d').values.tolist()
    line = (
        Line()
        .add_xaxis(x_data)
        # 主Y坐标轴（左边）
        .add_yaxis(
            # 图例显示
            title,
            # 数据
            (df[yaxis] / 100000000).apply(lambda x: '%.2f' % x).values.tolist(),
            # 定义bar柱体的颜色
            color=color,
            # 显示最高点的值
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
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
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
        )
    )

    return line


def line_component(df: pd.DataFrame, xaxis, yaxis: str, title: str, color: str = 'red') -> Line:
    x_data = df[xaxis].dt.strftime('%Y-%m-%d').values.tolist()

    line = (
        Line()
        .add_xaxis(x_data)
        .add_yaxis(
            title,
            df[yaxis].apply(lambda x: '%.2f' % x).values.tolist(),
            # 使用的 y 轴的 index，在单个图表实例中存在多个 y 轴的时候有用。
            # 因为使用的是副轴，所以为1（从0开始）
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            color=color,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")],
                                              label_opts=(LabelOpts(font_size=9))),
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