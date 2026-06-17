import streamlit as st
from datetime import date, timedelta
import pandas as pd
from utils.auth import require_login, current_user
from utils.db import get_client

st.set_page_config(page_title="Le mie ore", page_icon="🕒", layout="wide")
require_login()
user = current_user()
client = get_client()

GIORNI_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]


def lunedi_della_settimana(d: date) -> date:
    return d - timedelta(days=d.weekday())


def get_or_create_rapporto(dipendente_id: str, settimana_inizio: date):
    settimana_fine = settimana_inizio + timedelta(days=6)
    res = (
        client.table("rapporti_settimanali")
        .select("*")
        .eq("dipendente_id", dipendente_id)
        .eq("settimana_inizio", settimana_inizio.isoformat())
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]

    insert_res = (
        client.table("rapporti_settimanali")
        .insert(
            {
                "dipendente_id": dipendente_id,
                "settimana_inizio": settimana_inizio.isoformat(),
                "settimana_fine": settimana_fine.isoformat(),
                "stato": "in_corso",
            }
        )
        .execute()
    )
    return insert_res.data[0]


def get_righe(rapporto_id: str):
    res = (
        client.table("righe_lavoro")
        .select("*")
        .eq("rapporto_id", rapporto_id)
        .order("giorno")
        .order("ordine")
        .execute()
    )
    return res.data


def aggiungi_riga(rapporto_id: str, giorno: date, cliente: str, localita: str, ore: float, ordine: int):
    client.table("righe_lavoro").insert(
        {
            "rapporto_id": rapporto_id,
            "giorno": giorno.isoformat(),
            "cliente": cliente,
            "localita": localita,
            "ore": ore,
            "ordine": ordine,
        }
    ).execute()


def aggiorna_riga(riga_id: str, cliente: str, localita: str, ore: float):
    client.table("righe_lavoro").update(
        {"cliente": cliente, "localita": localita, "ore": ore}
    ).eq("id", riga_id).execute()


def elimina_riga(riga_id: str):
    client.table("righe_lavoro").delete().eq("id", riga_id).execute()


def aggiorna_stato(rapporto_id: str, stato: str):
    client.table("rapporti_settimanali").update({"stato": stato}).eq("id", rapporto_id).execute()


# --- Selezione settimana ---
st.title("🕒 Le mie ore")

oggi = date.today()
default_lunedi = lunedi_della_settimana(oggi)

col_a, col_b = st.columns([1, 3])
with col_a:
    settimana_scelta = st.date_input(
        "Seleziona una data nella settimana",
        value=default_lunedi,
        format="DD/MM/YYYY",
    )
settimana_inizio = lunedi_della_settimana(settimana_scelta)
settimana_fine = settimana_inizio + timedelta(days=6)

st.caption(f"Settimana: {settimana_inizio.strftime('%d/%m/%Y')} — {settimana_fine.strftime('%d/%m/%Y')}")

rapporto = get_or_create_rapporto(user["id"], settimana_inizio)

stato = rapporto["stato"]
stato_label = {
    "in_corso": "🟡 In corso",
    "inviato": "🔵 Inviato, in attesa di validazione",
    "validato": "🟢 Validato dal manager",
    "respinto": "🔴 Respinto — controlla le note e correggi",
}
st.markdown(f"**Stato rapporto:** {stato_label.get(stato, stato)}")

if rapporto.get("note_manager") and stato == "respinto":
    st.warning(f"Nota del manager: {rapporto['note_manager']}")

modificabile = stato in ("in_corso", "respinto")
if not modificabile:
    st.info("Questo rapporto è già stato inviato o validato. Per modificarlo dopo l'invio, chiedi al manager di riportarlo in stato 'in corso', oppure contattalo direttamente.")

righe = get_righe(rapporto["id"])

# --- Visualizzazione e editing per giorno ---
for i, nome_giorno in enumerate(GIORNI_IT):
    giorno_data = settimana_inizio + timedelta(days=i)
    st.markdown(f"### {nome_giorno} — {giorno_data.strftime('%d/%m/%Y')}")

    righe_giorno = [r for r in righe if r["giorno"] == giorno_data.isoformat()]

    if righe_giorno:
        for riga in righe_giorno:
            cols = st.columns([3, 3, 1, 1])
            with cols[0]:
                nuovo_cliente = st.text_input(
                    "Cliente", value=riga.get("cliente") or "", key=f"cliente_{riga['id']}",
                    disabled=not modificabile, label_visibility="collapsed", placeholder="Cliente"
                )
            with cols[1]:
                nuova_localita = st.text_input(
                    "Località", value=riga.get("localita") or "", key=f"localita_{riga['id']}",
                    disabled=not modificabile, label_visibility="collapsed", placeholder="Località"
                )
            with cols[2]:
                nuove_ore = st.number_input(
                    "Ore", value=float(riga.get("ore") or 0), step=0.5, min_value=0.0, max_value=24.0,
                    key=f"ore_{riga['id']}", disabled=not modificabile, label_visibility="collapsed"
                )
            with cols[3]:
                if modificabile and st.button("🗑️", key=f"del_{riga['id']}"):
                    elimina_riga(riga["id"])
                    st.rerun()

            if modificabile and (
                nuovo_cliente != (riga.get("cliente") or "")
                or nuova_localita != (riga.get("localita") or "")
                or nuove_ore != float(riga.get("ore") or 0)
            ):
                aggiorna_riga(riga["id"], nuovo_cliente, nuova_localita, nuove_ore)
                st.rerun()
    else:
        st.caption("Nessuna voce inserita per questo giorno.")

    if modificabile:
        with st.form(f"nuova_riga_{giorno_data.isoformat()}", clear_on_submit=True):
            cols = st.columns([3, 3, 1, 1])
            with cols[0]:
                cliente_input = st.text_input("Cliente", key=f"new_cliente_{i}", label_visibility="collapsed", placeholder="Cliente")
            with cols[1]:
                localita_input = st.text_input("Località", key=f"new_localita_{i}", label_visibility="collapsed", placeholder="Località")
            with cols[2]:
                ore_input = st.number_input("Ore", min_value=0.0, max_value=24.0, step=0.5, key=f"new_ore_{i}", label_visibility="collapsed")
            with cols[3]:
                submitted = st.form_submit_button("➕ Aggiungi")

            if submitted:
                ordine_nuovo = len(righe_giorno)
                aggiungi_riga(rapporto["id"], giorno_data, cliente_input, localita_input, ore_input, ordine_nuovo)
                st.rerun()

    st.divider()

# --- Totale settimanale e invio ---
totale_ore = sum(float(r.get("ore") or 0) for r in righe)
st.markdown(f"## Totale ore settimana: **{totale_ore:.2f}**")

if modificabile:
    if st.button("📨 Invia al manager per validazione", type="primary"):
        aggiorna_stato(rapporto["id"], "inviato")
        st.success("Rapporto inviato al manager.")
        st.rerun()
else:
    st.caption("Per riaprire la modifica dopo l'invio, contatta il manager.")
