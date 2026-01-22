import streamlit as st
from i18n import t


st.set_page_config(
    page_title=t("app.title"),
    page_icon="💰",
    layout="wide"
)

pg = st.navigation([
    st.Page("pages/overview.py", title=t("app.nav_overview"), icon="📊"),
    st.Page("pages/person_detail.py", title=t("app.nav_person"), icon="👤"),
    st.Page("pages/file_analysis.py", title=t("app.nav_file"), icon="📁"),
])
pg.run()
