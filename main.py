import streamlit as st

repo_page = st.Page("files/repo.py", title="回购业务", icon=":material/monitoring:")
ibo_page = st.Page("files/ibo.py", title="拆借业务", icon=":material/leaderboard:")

pg = st.navigation(
    {
        "业务概况": [repo_page, ibo_page],
    }
)
pg.run()
