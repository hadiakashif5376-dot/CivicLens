"""Entry point. On Streamlit Community Cloud set the main file to streamlit_app.py."""
import streamlit as st

st.set_page_config(page_title="CivicLens", page_icon="🏙️", layout="wide")

from civiclens.ui import bootstrap, session  # noqa: E402  (after set_page_config, which must run first)
from civiclens.ui.pages import citizen, login, officer  # noqa: E402

settings = bootstrap.init()
user = session.current_user()
session.sidebar_account(user)

if settings.is_demo_storage:
    st.warning("Demo storage: data is lost whenever the app restarts. Add a DATABASE_URL secret to keep it.")

if user is None:
    login.render(settings)
elif user.role == "officer":
    officer.render(user, settings)
else:
    citizen.render(user, settings)
