import streamlit as st
import secrets
import string
from utils.auth import require_manager, hash_password
from utils.db import get_client
from utils.ui import mostra_logo

st.set_page_config(page_title="Gestione dipendenti", page_icon="👥", layout="wide")
require_manager()
mostra_logo()
client = get_client()

st.title("👥 Gestione dipendenti")


def genera_password_temporanea(lunghezza=10):
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(lunghezza))


def get_dipendenti():
    res = client.table("dipendenti").select("*").order("cognome").execute()
    return res.data


# --- Crea nuovo dipendente ---
st.subheader("Aggiungi nuovo dipendente")

with st.form("nuovo_dipendente", clear_on_submit=True):
    cols = st.columns(4)
    with cols[0]:
        nome = st.text_input("Nome")
    with cols[1]:
        cognome = st.text_input("Cognome")
    with cols[2]:
        username = st.text_input("Nome utente")
    with cols[3]:
        is_manager = st.checkbox("È manager")

    submitted = st.form_submit_button("➕ Crea dipendente")

if submitted:
    if not nome or not cognome or not username:
        st.error("Compila nome, cognome e nome utente.")
    else:
        esistente = client.table("dipendenti").select("id").eq("username", username).execute()
        if esistente.data:
            st.error("Questo nome utente è già in uso, scegline un altro.")
        else:
            password_temp = genera_password_temporanea()
            client.table("dipendenti").insert(
                {
                    "nome": nome,
                    "cognome": cognome,
                    "username": username,
                    "password_hash": hash_password(password_temp),
                    "is_manager": is_manager,
                    "attivo": True,
                }
            ).execute()
            st.success(
                f"Dipendente creato. Comunica queste credenziali temporanee a {nome} {cognome}:\n\n"
                f"**Nome utente:** {username}\n\n**Password temporanea:** {password_temp}\n\n"
                "Consiglia di cambiarla subito dalla pagina 'Cambia password'."
            )

st.divider()

# --- Lista e gestione dipendenti esistenti ---
st.subheader("Dipendenti esistenti")

dipendenti = get_dipendenti()

for d in dipendenti:
    cols = st.columns([2, 2, 1, 1, 1, 1])
    with cols[0]:
        st.write(f"**{d['nome']} {d['cognome']}**")
    with cols[1]:
        st.write(d["username"])
    with cols[2]:
        st.write("Manager" if d["is_manager"] else "Dipendente")
    with cols[3]:
        st.write("🟢 Attivo" if d["attivo"] else "🔴 Disattivato")
    with cols[4]:
        if d["attivo"]:
            if st.button("Disattiva", key=f"deact_{d['id']}"):
                client.table("dipendenti").update({"attivo": False}).eq("id", d["id"]).execute()
                st.rerun()
        else:
            if st.button("Riattiva", key=f"react_{d['id']}"):
                client.table("dipendenti").update({"attivo": True}).eq("id", d["id"]).execute()
                st.rerun()
    with cols[5]:
        if st.button("Reset password", key=f"reset_{d['id']}"):
            nuova_temp = genera_password_temporanea()
            client.table("dipendenti").update({"password_hash": hash_password(nuova_temp)}).eq("id", d["id"]).execute()
            st.success(f"Nuova password temporanea per {d['nome']}: **{nuova_temp}**")
