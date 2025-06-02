import streamlit as st
from datetime import datetime
import json
import os

FIXKOSTEN_DATEI = "fixkosten.json"

st.set_page_config(page_title="Haushaltsrechner", layout="centered")

# --- Eingaben ---
st.title("📊 Haushaltsrechner")

heute = datetime.today()
aktuelles_datum = st.date_input("📅 Datum auswählen", heute)
aktueller_tag = aktuelles_datum.day
aktueller_monat = aktuelles_datum.month

aktuelles_geld = st.number_input("💶 Aktuell verfügbares Geld", min_value=0.0, step=1.0)

sparziel = st.number_input("💰 Sparziel für diesen Monat", min_value=0.0, step=1.0)

# --- Fixkosten laden ---
def lade_fixkosten():
    if not os.path.exists(FIXKOSTEN_DATEI):
        return []

    with open(FIXKOSTEN_DATEI, "r", encoding="utf-8") as f:
        fixkosten = json.load(f)
    return [eintrag for eintrag in fixkosten if aktueller_monat in eintrag["monat"]]

fixkosten = lade_fixkosten()
offene_fixkosten = [
    eintrag for eintrag in fixkosten if eintrag["tag"] >= aktueller_tag
]

fixkosten_summe = sum(abs(e["betrag"]) for e in offene_fixkosten)

# --- Ausgabe ---
if st.button("🧾 Haushaltsplan berechnen"):
    geld_nach_fixkosten = aktuelles_geld - fixkosten_summe
    geld_nach_sparziel = geld_nach_fixkosten - sparziel

    if geld_nach_fixkosten < 0:
        st.error("❌ Dein Geld reicht nicht für die Fixkosten!")
    elif geld_nach_sparziel < 0:
        st.warning("⚠️ Dein Sparziel ist zu hoch – es bleibt nichts mehr übrig.")
    else:
        st.success("✅ Berechnung erfolgreich!")

        st.write(f"📋 Fixkosten gesamt: **{fixkosten_summe:.2f} €**")
        st.write(f"💰 Nach Sparziel verbleibend: **{geld_nach_sparziel:.2f} €**")

        # Zeige kommende Fixkosten
        if offene_fixkosten:
            st.subheader("🗓 Kommende Fixkosten:")
            for eintrag in sorted(offene_fixkosten, key=lambda x: x["tag"]):
                st.markdown(f"- {eintrag['tag']:02d}.{aktueller_monat:02d}: **{eintrag['beschreibung']}** – {abs(eintrag['betrag']):.2f} €")
        else:
            st.info("🎉 Keine weiteren Fixkosten im aktuellen Monat.")

