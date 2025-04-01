import streamlit as st
import re
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Calcolo Ore Lavorate", layout="wide")

st.title("🕓 Calcolatore Ore Lavorate (Discord Logs)")
st.markdown("Incolla i messaggi di log qui sotto. Verranno conteggiate solo le ore tra le 09:59 e le 02:00 del giorno successivo. Le ore fuori fascia saranno riportate separatamente.")

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
    giorno_base = datetime.now().date()

    for riga in righe:
        riga = riga.strip()
        if not riga:
            continue

        match = re.match(r"^(.+?)\s+[—-]\s+.*$", riga)
        if match:
            persona_corrente = match.group(1).strip()

        if any(k in riga.lower() for k in ["inizio", "fine", "pausa", "rientro", "torno"]):
            orario = estrai_orario_da_testo(riga)
            if persona_corrente and orario:
                tipo = riga.lower()
                ts = datetime.combine(giorno_base, orario.time())
                if ts.time().hour < 6:
                    ts += timedelta(days=1)  # dopo mezzanotte
                if any(k in tipo for k in ["inizio", "rientro", "torno"]):
                    eventi.append((persona_corrente, "inizio", ts))
                elif any(k in tipo for k in ["fine", "pausa"]):
                    eventi.append((persona_corrente, "fine", ts))

    persone = defaultdict(list)
    for persona, tipo, orario in eventi:
        persone[persona].append((tipo, orario))

    risultati = {}
    fuori_fascia = {}

    ora_inizio = datetime.combine(giorno_base, datetime.strptime("09:59", "%H:%M").time())
    ora_fine = datetime.combine(giorno_base + timedelta(days=1), datetime.strptime("02:00", "%H:%M").time())

    for persona, logs in persone.items():
        logs.sort(key=lambda x: x[1])
        intervalli = []
        extra = []
        inizio = None

        for tipo, orario in logs:
            if tipo == "inizio":
                inizio = orario
            elif tipo == "fine" and inizio:
                fine = orario
                durata = fine - inizio
                if durata.total_seconds() > 0:
                    # Tagliare se parzialmente fuori fascia
                    start = max(inizio, ora_inizio)
                    end = min(fine, ora_fine)
                    durata_valida = max(timedelta(), end - start)
                    durata_extra = durata - durata_valida
                    if durata_valida:
                        intervalli.append(durata_valida)
                    if durata_extra:
                        extra.append(durata_extra)
                inizio = None

        totale = sum(intervalli, timedelta())
        extra_tot = sum(extra, timedelta())

        ore = totale.total_seconds() // 3600
        minuti = (totale.total_seconds() % 3600) // 60
        durata_formattata = f"{int(ore)},{int(minuti):02d}"
        check = ":approved:" if ore > 2 or (ore == 2 and minuti >= 30) else ""

        risultati[persona] = (durata_formattata, check)

        if extra_tot > timedelta():
            ore_extra = extra_tot.total_seconds() // 3600
            min_extra = (extra_tot.total_seconds() % 3600) // 60
            fuori_fascia[persona] = f"{int(ore_extra)},{int(min_extra):02d}"

    return risultati, fuori_fascia

if st.button("🔍 Calcola Ore"):
    if testo.strip() == "":
        st.warning("Per favore, incolla del testo nei messaggi.")
    else:
        risultati, fuori_fascia = calcola_ore(testo)
        st.subheader("📊 Risultati")
        for persona, (durata, check) in sorted(risultati.items(), key=lambda x: x[0].lower()):
            st.write(f"**{persona}**: {durata}h {check}")

        if fuori_fascia:
            st.subheader("⛔ Orario fuori fascia")
            for persona, durata in sorted(fuori_fascia.items(), key=lambda x: x[0].lower()):
                st.write(f"**{persona}**: {durata}h")
