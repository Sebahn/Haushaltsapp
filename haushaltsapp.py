# Haushaltsrechner als Streamlit App
import streamlit as st
import json
import os
from datetime import datetime, timedelta
from calendar import monthrange

# --- Konfiguration ---
FIXKOSTEN_DATEI = "fixkosten.json"
DURCHSCHNITT_LEBENSMITTEL_PRO_TAG = 7  # EUR
FRAGEZEITRAUM_TAGE = 7
RUECKWIRKENDE_ABFRAGE_GRENZE_TAGE = 3

# --- Titel und Einführung ---
st.set_page_config(page_title="Haushaltsrechner", layout="centered")
st.title("💸 Haushaltsrechner")

# --- Datumsauswahl ---
datum_modus = st.radio("📅 Möchtest du das heutige Datum nutzen oder ein Datum simulieren?", ["heute", "simulieren"])

if datum_modus == "simulieren":
    eingabe_datum = st.date_input("Bitte wähle ein Datum", value=datetime.today())
else:
    eingabe_datum = datetime.today()

heute = eingabe_datum
aktueller_tag = heute.day
aktueller_monat = heute.month
aktuelles_jahr = heute.year
resttage = monthrange(aktuelles_jahr, aktueller_monat)[1] - aktueller_tag
letzter_tag_monat = monthrange(aktuelles_jahr, aktueller_monat)[1]

# --- Fixkosten laden ---
def lade_fixkosten():
    fixkosten_summe = 0
    aufgeführte_fixkosten = []

    if not os.path.exists(FIXKOSTEN_DATEI):
        return 0, []

    with open(FIXKOSTEN_DATEI, "r", encoding="utf-8") as f:
        fixkosten = json.load(f)
        for eintrag in fixkosten:
            if aktueller_monat in eintrag["monat"]:
                fix_tag = eintrag["tag"]
                beschreibung = eintrag["beschreibung"]
                betrag = abs(eintrag["betrag"])
                abfrage = eintrag.get("abfrage", True)

                if fix_tag > aktueller_tag:
                    if abfrage and (fix_tag - aktueller_tag) <= FRAGEZEITRAUM_TAGE:
                        antwort = st.radio(f"🔔 Fixkosten '{beschreibung}' ({betrag:.2f} EUR) am {fix_tag}.{aktueller_monat}. Noch aktuell?", ["ja", "nein"], key=f"zukunft_{beschreibung}")
                        if antwort == "ja":
                            fixkosten_summe += betrag
                            aufgeführte_fixkosten.append((fix_tag, beschreibung, betrag))
                    else:
                        fixkosten_summe += betrag
                        aufgeführte_fixkosten.append((fix_tag, beschreibung, betrag))

                elif fix_tag == aktueller_tag:
                    antwort = st.radio(f"🔔 Fixkosten '{beschreibung}' ({betrag:.2f} EUR) heute fällig. Schon abgebucht?", ["ja", "nein"], key=f"heute_{beschreibung}")
                    if antwort == "nein":
                        fixkosten_summe += betrag
                        aufgeführte_fixkosten.append((fix_tag, beschreibung, betrag))

                elif 0 < (aktueller_tag - fix_tag) <= RUECKWIRKENDE_ABFRAGE_GRENZE_TAGE:
                    antwort = st.radio(f"🕑 Fixkosten '{beschreibung}' ({betrag:.2f} EUR) war am {fix_tag}.{aktueller_monat}. Schon abgebucht?", ["ja", "nein"], key=f"vergangen_{beschreibung}")
                    if antwort == "nein":
                        fixkosten_summe += betrag
                        aufgeführte_fixkosten.append((fix_tag, beschreibung, betrag))

    return fixkosten_summe, aufgeführte_fixkosten

# --- Hauptablauf ---
aktuelles_geld_input = st.text_input("💶 Wie viel Geld hast du aktuell verfügbar? (z.B. 500,50)", value="")

if aktuelles_geld_input:
    try:
        aktuelles_geld = float(aktuelles_geld_input.replace(",", "."))
        fixkosten_summe, liste_fixkosten = lade_fixkosten()

        st.subheader("📋 Berücksichtigte Fixkosten bis Monatsende")
        if liste_fixkosten:
            for tag, text, betrag in sorted(liste_fixkosten):
                st.write(f"→ {tag:02d}.{aktueller_monat:02d}: {text} – {betrag:.2f} EUR")
        else:
            st.info("Keine weiteren Fixkosten bis Monatsende gefunden.")

        zusatzkosten_input = st.text_input("📋 Planst du in den nächsten 5 Tagen neue größere Ausgaben? (optional, z.B. 100)", value="0")
        try:
            zusatzkosten = float(zusatzkosten_input.replace(",", "."))
        except:
            zusatzkosten = 0

        gesamt_fixkosten = fixkosten_summe + zusatzkosten
        geld_nach_fixkosten = aktuelles_geld - gesamt_fixkosten

        if geld_nach_fixkosten <= 0:
            st.error("🚨 Achtung: Dein Geld reicht nicht für die kommenden Fixkosten!")
        else:
            sparziel_input = st.text_input("💰 Wie viel möchtest du diesen Monat noch sparen?", value="0")
            try:
                sparziel = float(sparziel_input.replace(",", "."))
                geld_nach_sparziel = geld_nach_fixkosten - sparziel
                lebensmittelbedarf = resttage * DURCHSCHNITT_LEBENSMITTEL_PRO_TAG
                geld_nach_lebensmittel = geld_nach_sparziel - lebensmittelbedarf
                freies_tagesbudget = geld_nach_lebensmittel / resttage if resttage > 0 else 0

                # Ausgabe Finanzplan
                st.subheader("🧾 Dein Finanzplan")
                st.write(f"Fixkosten gesamt            : {gesamt_fixkosten:.2f} €")
                st.write(f"Sparziel reserviert         : {sparziel:.2f} €")
                st.write(f"Lebensmittelbedarf geschätzt: {lebensmittelbedarf:.2f} €")
                st.success(f"✅ Freies Geld für Extras    : {geld_nach_lebensmittel:.2f} €")
                st.info(f"📅 Tagesbudget für Extras: {freies_tagesbudget:.2f} € pro Tag")

            except:
                st.error("❌ Ungültiges Sparziel eingegeben.")

    except:
        st.error("❌ Ungültiger Betrag bei verfügbarem Geld.")

