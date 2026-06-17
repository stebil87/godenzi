import bcrypt
import streamlit as st
from utils.db import get_client


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def get_user_by_username(username: str):
    client = get_client()
    res = (
        client.table("dipendenti")
        .select("*")
        .eq("username", username)
        .eq("attivo", True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def login(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if user is None:
        return False
    if verify_password(password, user["password_hash"]):
        st.session_state["user"] = user
        return True
    return False


def logout():
    if "user" in st.session_state:
        del st.session_state["user"]


def current_user():
    return st.session_state.get("user")


def require_login():
    """Da chiamare in cima a ogni pagina. Blocca se non loggato."""
    if current_user() is None:
        st.warning("Devi accedere per vedere questa pagina.")
        st.stop()


def require_manager():
    require_login()
    user = current_user()
    if not user.get("is_manager"):
        st.error("Accesso riservato al manager.")
        st.stop()


def change_password(user_id: str, new_password: str):
    client = get_client()
    new_hash = hash_password(new_password)
    client.table("dipendenti").update({"password_hash": new_hash}).eq(
        "id", user_id
    ).execute()
