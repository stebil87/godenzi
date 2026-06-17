"""
Script eseguito automaticamente la domenica via GitHub Actions.
Genera il PDF per ogni rapporto della settimana corrente e lo carica
su Supabase Storage, salvando l'URL nel record del rapporto.
"""
import os
import sys
from datetime import date, timedelta
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.pdf_generator import genera_pdf_settimanale

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET = "rapporti-pdf"

client = create_client(SUPABASE_URL, SUPABASE_KEY)


def lunedi_della_settimana(d: date) -> date:
    return d - timedelta(days=d.weekday())


def main():
    oggi = date.today()
    settimana_inizio = lunedi_della_settimana(oggi)

    rapporti = (
        client.table("rapporti_settimanali")
        .select("*")
        .eq("settimana_inizio", settimana_inizio.isoformat())
        .execute()
        .data
    )

    if not rapporti:
        print("Nessun rapporto trovato per questa settimana.")
        return

    dipendenti = {d["id"]: d for d in client.table("dipendenti").select("*").execute().data}

    for rapporto in rapporti:
        dipendente = dipendenti.get(rapporto["dipendente_id"])
        if not dipendente:
            continue

        righe = (
            client.table("righe_lavoro")
            .select("*")
            .eq("rapporto_id", rapporto["id"])
            .order("giorno")
            .order("ordine")
            .execute()
            .data
        )

        pdf_bytes = genera_pdf_settimanale(dipendente, rapporto, righe)

        path = f"{settimana_inizio.isoformat()}/{dipendente['username']}.pdf"
        client.storage.from_(BUCKET).upload(
            path, pdf_bytes, {"content-type": "application/pdf", "upsert": "true"}
        )
        public_url = client.storage.from_(BUCKET).get_public_url(path)

        client.table("rapporti_settimanali").update({"pdf_url": public_url}).eq(
            "id", rapporto["id"]
        ).execute()

        print(f"PDF generato per {dipendente['nome']} {dipendente['cognome']}: {public_url}")


if __name__ == "__main__":
    main()
