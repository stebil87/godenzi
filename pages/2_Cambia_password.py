import streamlit as st
from utils.auth import require_login, current_user, verify_password, change_password
from utils.ui import mostra_logo

st.set_page_config(page_title="Cambia password", page_icon="🔑")
require_login()
mostra_logo()
user = current_user()

st.title("🔑 Cambia la tua password")

with st.form("cambia_password"):
    vecchia = st.text_input("Password attuale", type="password")
    nuova = st.text_input("Nuova password", type="password")
    conferma = st.text_input("Conferma nuova password", type="password")
    submitted = st.form_submit_button("Aggiorna password")

if submitted:
    if not verify_password(vecchia, user["password_hash"]):
        st.error("La password attuale non è corretta.")
    elif len(nuova) < 6:
        st.error("La nuova password deve avere almeno 6 caratteri.")
    elif nuova != conferma:
        st.error("Le due password non coincidono.")
    else:
        change_password(user["id"], nuova)
        st.success("Password aggiornata con successo. Verrà usata dal prossimo accesso.")
