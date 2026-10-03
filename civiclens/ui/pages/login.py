import streamlit as st
from pydantic import ValidationError

from ...core.config import Settings
from ...core.errors import ServiceError, validation_message
from ...core.schemas import RegisterIn
from ...core.services import auth
from .. import session


def render(settings: Settings) -> None:
    st.title("CivicLens")
    st.write("Report a city problem and follow it until it is fixed. City officers sign in to review and assign reports.")
    if not settings.officer_email:
        st.warning("No officer account is set up yet. Add OFFICER_EMAIL and OFFICER_PASSWORD to the app secrets.")

    sign_in_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            try:
                user = auth.authenticate(email, password)
            except ServiceError as exc:
                st.error(str(exc))
            else:
                session.sign_in(user)
                st.rerun()

    with register_tab:
        with st.form("register"):
            full_name = st.text_input("Full name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password (at least 8 characters)", type="password", key="reg_password")
            created = st.form_submit_button("Create account", type="primary")
        if created:
            try:
                user = auth.register_citizen(RegisterIn(email=reg_email, full_name=full_name, password=reg_password))
            except ValidationError as exc:
                st.error(validation_message(exc))
            except ServiceError as exc:
                st.error(str(exc))
            else:
                session.sign_in(user)
                st.rerun()
