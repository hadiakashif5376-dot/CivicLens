"""Who is signed in, plus one-time messages and form resets. All state lives in st.session_state."""
from typing import Optional

import streamlit as st

from ..core.schemas import UserOut

_USER = "user"
_FLASH = "flash"
_FORM = "form_nonce"


def current_user() -> Optional[UserOut]:
    return st.session_state.get(_USER)


def sign_in(user: UserOut) -> None:
    st.session_state[_USER] = user


def sign_out() -> None:
    st.session_state.clear()


def flash(message: str, kind: str = "success") -> None:
    """Show a message on the next run, for example right after st.rerun()."""
    st.session_state[_FLASH] = (kind, message)


def show_flash() -> None:
    item = st.session_state.pop(_FLASH, None)
    if item:
        kind, message = item
        getattr(st, kind)(message)


def form_nonce() -> int:
    """Put this in a form's key. Bumping it gives the user a fresh, empty form."""
    return st.session_state.get(_FORM, 0)


def bump_form() -> None:
    st.session_state[_FORM] = form_nonce() + 1


def sidebar_account(user: Optional[UserOut]) -> None:
    with st.sidebar:
        st.markdown("### CivicLens")
        if user is None:
            st.caption("Smart city complaint handling")
            return
        st.caption(f"{user.full_name} · {user.role}")
        st.button("Sign out", on_click=sign_out)
