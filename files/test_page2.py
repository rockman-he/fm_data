import streamlit as st
from pyecharts.charts import Bar
from pyecharts import options as opts
from streamlit.components.v1 import html


# 创建一个简单的柱状图
def create_pyecharts_chart():
    bar = (
        Bar()
        .add_xaxis(["Apple", "Banana", "Orange", "Grapes", "Watermelon"])
        .add_yaxis("Sales", [10, 20, 15, 8, 25])
        .set_global_opts(title_opts=opts.TitleOpts(title="Fruit Sales"))
    )
    return bar


# 获取 pyecharts 图表的 HTML 内容
chart = create_pyecharts_chart()
chart_html = chart.render_embed()

# 使用 Streamlit 显示 HTML
st.title("Pyecharts in Streamlit")

html(chart_html, height=500)
