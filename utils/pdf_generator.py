from io import BytesIO
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, BaseDocTemplate, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

GIORNI_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]


def _righe_per_giorno(righe, giorno_iso):
    return [r for r in righe if r["giorno"] == giorno_iso]


def _tabella_giorni(giorni_idx, settimana_inizio, righe, col_widths):
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle("header", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9)
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8)

    data_rows = [["Data", "Cliente", "Località", "Ore"]]
    span_rows = []  # righe (index) dove scrivere il nome del giorno in grassetto
    riga_idx = 1

    for gi in giorni_idx:
        giorno_data = settimana_inizio + timedelta(days=gi)
        nome_giorno = GIORNI_IT[gi]
        righe_giorno = _righe_per_giorno(righe, giorno_data.isoformat())

        n_righe_minime = 4  # minimo righe visualizzate per giorno, anche se vuoto
        n_righe = max(len(righe_giorno), n_righe_minime)

        totale_giorno = sum(float(r.get("ore") or 0) for r in righe_giorno)

        for r_i in range(n_righe):
            if r_i < len(righe_giorno):
                r = righe_giorno[r_i]
                cliente = r.get("cliente") or ""
                localita = r.get("localita") or ""
                ore = r.get("ore")
                ore_str = f"{float(ore):.2f}" if ore else ""
            else:
                cliente, localita, ore_str = "", "", ""

            primo = r_i == 0
            label = nome_giorno if primo else ""
            data_rows.append([label, cliente, localita, ore_str])
            if primo:
                span_rows.append(riga_idx)
            riga_idx += 1

        # riga totale del giorno
        data_rows.append(["", "", "Tot.", f"{totale_giorno:.2f}"])
        riga_idx += 1

    table = Table(data_rows, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
    ]
    for r in span_rows:
        style_cmds.append(("FONTNAME", (0, r), (0, r), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_cmds))
    return table


def genera_pdf_settimanale(dipendente: dict, rapporto: dict, righe: list, logo_path: str = None) -> bytes:
    buffer = BytesIO()
    page_size = landscape(A4)
    doc = BaseDocTemplate(buffer, pagesize=page_size, leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=13)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10)

    settimana_inizio = date.fromisoformat(rapporto["settimana_inizio"])
    settimana_fine = date.fromisoformat(rapporto["settimana_fine"])

    elements = []
    elements.append(Paragraph("IVO GODENZI &nbsp;&nbsp; LATTONIERE", title_style))
    elements.append(Paragraph("RIVA S. VITALE", sub_style))
    elements.append(Paragraph("&nbsp;", sub_style))
    elements.append(
        Paragraph(
            f"Rapporto di lavoro &nbsp;&nbsp; dal {settimana_inizio.strftime('%d/%m/%Y')} "
            f"&nbsp;&nbsp; al {settimana_fine.strftime('%d/%m/%Y')} "
            f"&nbsp;&nbsp;&nbsp;&nbsp; Nome: {dipendente['nome']} {dipendente['cognome']}",
            sub_style,
        )
    )
    elements.append(Paragraph("&nbsp;", sub_style))

    col_widths_half = [2.2*cm, 6*cm, 6*cm, 1.8*cm]

    tabella_sx = _tabella_giorni([0, 1, 2], settimana_inizio, righe, col_widths_half)
    tabella_dx = _tabella_giorni([3, 4, 5], settimana_inizio, righe, col_widths_half)

    due_colonne = Table(
        [[tabella_sx, tabella_dx]],
        colWidths=[doc.width / 2 - 0.3*cm, doc.width / 2 - 0.3*cm],
    )
    due_colonne.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(due_colonne)

    elements.append(Paragraph("&nbsp;", sub_style))
    totale_ore = sum(float(r.get("ore") or 0) for r in righe)
    elements.append(Paragraph(f"<b>TOTALE ORE SETTIMANA: {totale_ore:.2f}</b>", sub_style))

    if rapporto.get("stato") == "validato":
        elements.append(Paragraph(f"<i>Validato il {rapporto.get('validato_il', '')}</i>", sub_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
