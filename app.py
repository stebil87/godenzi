import streamlit as st
from datetime import date
from utils.auth import login, logout, current_user, hash_password
from utils.db import get_client

st.set_page_config(page_title="Godenzi Lattoniere - Rapporti di lavoro", page_icon="🔧", layout="wide")


def bootstrap_first_manager_if_needed():
    """Se la tabella dipendenti e' vuota, crea il primo manager usando i secrets."""
    client = get_client()
    res = client.table("dipendenti").select("id").limit(1).execute()
    if res.data:
        return  # esistono gia' utenti, non serve bootstrap

    admin_user = st.secrets.get("app", {}).get("admin_bootstrap_username")
    admin_pass = st.secrets.get("app", {}).get("admin_bootstrap_password")
    if not admin_user or not admin_pass:
        return

    client.table("dipendenti").insert(
        {
            "nome": "Ivo",
            "cognome": "Godenzi",
            "username": admin_user,
            "password_hash": hash_password(admin_pass),
            "is_manager": True,
        }
    ).execute()
    st.info(
        f"Primo accesso configurato. Utente manager '{admin_user}' creato. "
        "Accedi e cambia la password dal tuo portale."
    )


def login_form():
    st.title("🔧 Godenzi Lattoniere — Rapporti di lavoro")
    st.subheader("Accesso")

    with st.form("login_form"):
        username = st.text_input("Nome utente")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi")

    if submitted:
        if login(username, password):
            st.rerun()
        else:
            st.error("Nome utente o password non corretti.")


def main():
    bootstrap_first_manager_if_needed()

    user = current_user()

    if user is None:
        login_form()
        return

    # Sidebar con info utente e logout
    with st.sidebar:
        st.markdown(f"**{user['nome']} {user['cognome']}**")
        ruolo = "Manager" if user["is_manager"] else "Dipendente"
        st.caption(ruolo)
        if st.button("Esci"):
            logout()
            st.rerun()

    st.title("🔧 Godenzi Lattoniere")
    st.write(f"Ciao {user['nome']}, usa il menu a sinistra per navigare.")
    st.markdown(
        """
        - **Le mie ore**: inserisci qui le ore lavorate giorno per giorno.
        - **Cambia password**: aggiorna la tua password personale.
        """
    )
    if user["is_manager"]:
        st.markdown("- **Validazione**: rivedi e valida i rapporti dei dipendenti.")


if __name__ == "__main__":
    main()
