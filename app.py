import streamlit as st
import re
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Calcolo Ore Lavorate", layout="wide")

st.title("🕓 Calcolatore Ore Lavorate (Discord Logs)")
st.markdown("Incolla i messaggi di log qui sotto. Il sistema leggerà l'orario direttamente dal messaggio (es. `inizio 17.25`) e calcolerà le ore lavorate per ciascuno.")

testo = st.text_area("📋 Inserisci il testo dei messaggi:", height=400)

def estrai_orario_da_testo(testo):
    match = re.search(r"(\d{1,2}[:.]\d{2})", testo)
    if match:
        t = match.group(1).replace(".", ":")
        return datetime.strptime(t, "%H:%M")
    return None

def calcola_ore(testo):
    righe = testo.strip().split("\n")
    eventi = []
    persona_corrente = None

    for riga in righe:
        riga = riga.strip()
        if not riga:
            continue

        # Se è una riga con il nome utente (aggiorna il riferimento)
        match = re.match(r"^(.+?)\s+[—-]\s+.*$", riga)
        if match:
            persona_corrente = match.group(1).strip()

        # Se è una riga con tipo evento + orario
        if any(k in riga.lower() for k in ["inizio", "fine", "pausa", "rientro", "torno"]):
            orario = estrai_orario_da_testo(riga)
            if persona_corrente and orario:
                tipo = riga.lower()
                if any(k in tipo for k in ["inizio", "rientro", "torno"]):
                    eventi.append((persona_corrente, "inizio", orario))
                elif any(k in tipo for k in ["fine", "pausa"]):
                    eventi.append((persona_corrente, "fine", orario))

    # Organizza per persona
    persone = defaultdict(list)
    for persona, tipo, orario in eventi:
        persone[persona].append((tipo, orario))

    risultati = {}

    for persona, logs in persone.items():
        logs.sort(key=lambda x: x[1])  # Ordina per orario
        intervalli = []
        inizio = None

        for tipo, orario in logs:
            if tipo == "inizio":
                inizio = orario
            elif tipo == "fine" and inizio:
                durata = orario - inizio
                if durata.total_seconds() > 0:
                    intervalli.append(durata)
                inizio = None

        totale = sum(intervalli, timedelta())
        ore = totale.seconds // 3600
        minuti = (totale.seconds % 3600) // 60
        durata_formattata = f"{ore}.{minuti:02d}"
        check = "✅" if ore > 2 or (ore == 2 and minuti >= 30) else "❌"
        risultati[persona] = (durata_formattata, check)

    return risultati

if st.button("🔍 Calcola Ore"):
    if testo.strip() == "":
        st.warning("Per favore, incolla del testo nei messaggi.")
    else:
        risultati = calcola_ore(testo)
        st.subheader("📊 Risultati")
        for persona, (durata, check) in sorted(risultati.items(), key=lambda x: x[0].lower()):
            st.write(f"**{persona}**: {durata}h {check}")
