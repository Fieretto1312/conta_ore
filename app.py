import streamlit as st
import re
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Calcolo Ore Lavorate", layout="wide")

st.title("🕓 Calcolatore Ore Lavorate (Discord Logs)")
st.markdown("Incolla i messaggi di log qui sotto. Il sistema calcolerà le ore lavorate per ciascuno e assegnerà ✅ o ❌ in base alla soglia 2.30h.")

testo = st.text_area("📋 Inserisci il testo dei messaggi:", height=400)

def parse_timestamp(stringa, data_base):
    """Gestisce conversione di 'Yesterday at 22:00' e '00:30' in datetime corretti"""
    stringa = stringa.strip()
    if "yesterday at" in stringa.lower():
        orario = re.search(r"yesterday at (\d{1,2}[:.]\d{2})", stringa.lower())
        if orario:
            t = orario.group(1).replace(".", ":")
            dt = datetime.strptime(t, "%H:%M")
            ieri = datetime.now().date() - timedelta(days=1)
            return datetime.combine(ieri, dt.time())
    else:
        orario = re.search(r"(\d{1,2}[:.]\d{2})", stringa)
        if orario:
            t = orario.group(1).replace(".", ":")
            dt = datetime.strptime(t, "%H:%M")
            giorno = data_base
            if dt.time() < datetime.strptime("06:00", "%H:%M").time():
                # dopo la mezzanotte → giorno successivo
                giorno += timedelta(days=1)
            return datetime.combine(giorno, dt.time())
    return None

def calcola_ore(testo):
    righe = testo.strip().split("\n")
    eventi = []  # Lista di (persona, tipo_evento, timestamp)

    persona_corrente = None
    data_corrente = datetime.now().date()  # Partiamo da oggi

    for riga in righe:
        riga = riga.strip()
        if not riga:
            continue

        # Controllo se è una riga con "—" e orario
        match = re.match(r"^(.*?)[—-]\s*(.*)$", riga)
        if match:
            persona_corrente = match.group(1).strip()
            timestamp_raw = match.group(2).strip()
            ts = parse_timestamp(riga, data_corrente)
            if ts:
                data_corrente = ts.date()
        else:
            tipo = riga.lower()
            ts = parse_timestamp(riga, data_corrente)
            if persona_corrente and ts:
                if any(k in tipo for k in ["inizio", "torno", "rientro"]):
                    eventi.append((persona_corrente, "inizio", ts))
                elif any(k in tipo for k in ["fine", "pausa"]):
                    eventi.append((persona_corrente, "fine", ts))

    # Organizza per persona
    persone = defaultdict(list)
    for persona, tipo, timestamp in eventi:
        persone[persona].append((tipo, timestamp))

    risultati = {}

    for persona, logs in persone.items():
        logs.sort(key=lambda x: x[1])  # Ordina per orario
        intervalli = []
        inizio = None

        for tipo, timestamp in logs:
            if tipo == "inizio":
                inizio = timestamp
            elif tipo == "fine" and inizio:
                durata = timestamp - inizio
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
