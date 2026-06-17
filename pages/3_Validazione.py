import streamlit as st
from datetime import date, timedelta
from utils.auth import require_manager, current_user
from utils.db import get_client
from utils.pdf_generator import genera_pdf_settimanale
from utils.ui import mostra_logo

st.set_page_config(page_title="Validazione rapporti", page_icon="✅", layout="wide")
require_manager()
mostra_logo()
manager = current_user()
client = get_client()


def lunedi_della_settimana(d: date) -> date:
    return d - timedelta(days=d.weekday())


@st.cache_data(ttl=10)
def get_dipendenti():
    res = client.table("dipendenti").select("id, nome, cognome").eq("attivo", True).execute()
    return {d["id"]: f"{d['nome']} {d['cognome']}" for d in res.data}


def get_rapporti(settimana_inizio: date):
    res = (
        client.table("rapporti_settimanali")
        .select("*")
        .eq("settimana_inizio", settimana_inizio.isoformat())
        .execute()
    )
    return res.data


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


def aggiorna_stato(rapporto_id: str, stato: str, note: str = None):
    payload = {"stato": stato}
    if stato == "validato":
        payload["validato_da"] = manager["id"]
        payload["validato_il"] = "now()"
    if note is not None:
        payload["note_manager"] = note
    client.table("rapporti_settimanali").update(payload).eq("id", rapporto_id).execute()


st.title("✅ Validazione rapporti settimanali")

oggi = date.today()
settimana_scelta = st.date_input(
    "Seleziona una data nella settimana da revisionare",
    value=lunedi_della_settimana(oggi),
    format="DD/MM/YYYY",
)
settimana_inizio = lunedi_della_settimana(settimana_scelta)
settimana_fine = settimana_inizio + timedelta(days=6)
st.caption(f"Settimana: {settimana_inizio.strftime('%d/%m/%Y')} — {settimana_fine.strftime('%d/%m/%Y')}")

dipendenti_map = get_dipendenti()
rapporti = get_rapporti(settimana_inizio)

if not rapporti:
    st.info("Nessun rapporto trovato per questa settimana.")
else:
    stato_label = {
        "in_corso": "🟡 In corso",
        "inviato": "🔵 Inviato",
        "validato": "🟢 Validato",
        "respinto": "🔴 Respinto",
    }

    for rapporto in rapporti:
        nome_dipendente = dipendenti_map.get(rapporto["dipendente_id"], "Sconosciuto")
        righe = get_righe(rapporto["id"])
        totale_ore = sum(float(r.get("ore") or 0) for r in righe)

        with st.expander(f"{nome_dipendente} — {stato_label.get(rapporto['stato'], rapporto['stato'])} — {totale_ore:.2f} ore"):
            if righe:
                import pandas as pd
                df = pd.DataFrame(righe)[["giorno", "cliente", "localita", "ore"]]
                df.columns = ["Giorno", "Cliente", "Località", "Ore"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("Nessuna voce inserita.")

            note = st.text_area("Note per il dipendente", value=rapporto.get("note_manager") or "", key=f"note_{rapporto['id']}")

            cols = st.columns(4)
            with cols[0]:
                if st.button("✅ Valida", key=f"val_{rapporto['id']}"):
                    aggiorna_stato(rapporto["id"], "validato", note)
                    st.rerun()
            with cols[1]:
                if st.button("❌ Respingi", key=f"resp_{rapporto['id']}"):
                    aggiorna_stato(rapporto["id"], "respinto", note)
                    st.rerun()
            with cols[2]:
                if st.button("↩️ Riapri (in corso)", key=f"reopen_{rapporto['id']}"):
                    aggiorna_stato(rapporto["id"], "in_corso", note)
                    st.rerun()
            with cols[3]:
                dipendente_full = next((d for d in [{"id": k, "nome": v.split()[0], "cognome": " ".join(v.split()[1:])} for k, v in dipendenti_map.items()] if d["id"] == rapporto["dipendente_id"]), None)
                if st.button("📄 Genera PDF", key=f"pdf_{rapporto['id']}"):
                    pdf_bytes = genera_pdf_settimanale(dipendente_full, rapporto, righe)
                    st.download_button(
                        "⬇️ Scarica PDF",
                        data=pdf_bytes,
                        file_name=f"rapporto_{nome_dipendente.replace(' ', '_')}_{settimana_inizio.isoformat()}.pdf",
                        mime="application/pdf",
                        key=f"dl_{rapporto['id']}",
                    )
