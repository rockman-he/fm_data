import streamlit as st

repo_page = st.Page("files/repo.py", title="回购业务", icon=":material/monitoring:")
ibo_page = st.Page("files/ibo.py", title="拆借业务", icon=":material/leaderboard:")
bond_page = st.Page("files/bond.py", title="债券业务", icon=":material/leaderboard:")
test_page = st.Page("files/test_page.py", title="测试页面", icon=":material/leaderboard:")

pg = st.navigation(
    {
        "业务概况": [repo_page, ibo_page, bond_page, test_page]
    }
)
pg.run()
