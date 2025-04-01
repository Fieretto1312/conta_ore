import streamlit as st
import re
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Calcolo Ore Lavorate", layout="wide")

st.title("🕓 Calcolatore Ore Lavorate (Discord Logs)")
st.markdown("Incolla i messaggi di log qui sotto. Il sistema calcolerà le ore lavorate per ciascuno e assegnerà ✅ o ❌ in base alla soglia 2.30h.")

testo = st.text_area("📋 Inserisci il testo dei messaggi:", height=400)

def parse_time(t):
    try:
        return datetime.strptime(t.strip(), "%H.%M")
    except ValueError:
        return datetime.strptime(t.strip(), "%H:%M")

def calcola_ore(testo):
    pattern = r"^(.*?)[—-]\s*(\d{1,2}[:.]\d{2})$"
    righe = testo.strip().split("\n")

    persone = defaultdict(list)
    ultima_persona = None

    for riga in righe:
        match = re.match(pattern, riga.strip())
        if match:
            persona = match.group(1).strip()
            orario = parse_time(match.group(2))
            ultima_persona = persona
            persone[persona].append((orario, None))
        elif any(k in riga.lower() for k in ["inizio", "fine", "pausa", "torno"]):
            if ultima_persona and persone[ultima_persona]:
                persone[ultima_persona][-1] = (persone[ultima_persona][-1][0], riga.lower())

    risultati = {}

    for persona, eventi in persone.items():
        intervalli = []
        inizio = None
        for orario, tipo in eventi:
            if tipo and "inizio" in tipo:
                inizio = orario
            elif tipo and ("fine" in tipo or "pausa" in tipo):
                if inizio:
                    fine = orario
                    durata = fine - inizio
                    if durata.total_seconds() > 0:
                        intervalli.append(durata)
                    inizio = None
            elif tipo and "torno" in tipo:
                inizio = orario

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
