import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Konfiguration der Seite ---
st.set_page_config(page_title="Bohrprotokoll Profi", page_icon="💧", layout="wide")

st.title("💧 Bohrprotokoll: Langzeit-Pumpversuch")
st.markdown("Dokumentation über **9 Stunden** mit **15-Minuten-Intervallen**.")

# --- 1. Eingabe der Parameter ---
with st.sidebar:
    st.header("⚙️ Einstellungen")
    projekt_name = st.text_input("Projektname", "BV Müller - Brunnen 1")
    rws = st.number_input("Ruhewasserspiegel (m u. GOK)", value=2.10, step=0.01)
    q_soll = st.number_input("Förderleistung (m³/h)", value=5.0, step=0.1)
    
    st.markdown("---")
    pump_dauer_h = st.number_input("Pumpdauer (Stunden)", value=8, min_value=1)
    gesamt_dauer_h = st.number_input("Gesamtdauer (Stunden)", value=9, min_value=pump_dauer_h)
    
    # Umrechnung in Minuten
    pump_end_min = pump_dauer_h * 60
    gesamt_dauer_min = gesamt_dauer_h * 60

# --- 2. Automatische Generierung der Zeit-Intervalle ---
zeit_intervalle = list(range(0, gesamt_dauer_min + 1, 15))

# Dummy-Daten generieren
default_pegel = []
for t in zeit_intervalle:
    if t <= pump_end_min:
        # Absenkung
        wert = rws + (1.5 * np.log10(t + 1) / np.log10(pump_end_min + 1)) 
        if t == 0: wert = rws
    else:
        # Wiederanstieg
        time_recovery = t - pump_end_min
        wert = default_pegel[-1] - (default_pegel[-1] - rws) * (time_recovery / 120)
        if wert < rws: wert = rws
    default_pegel.append(round(wert, 2))

df_template = pd.DataFrame({
    "Zeit [min]": zeit_intervalle,
    "Wasserstand [m]": default_pegel
})

# --- 3. Dateneingabe ---
st.subheader("📝 Messwerte eingeben")
edited_df = st.data_editor(df_template, height=250, use_container_width=True, num_rows="dynamic")

# --- 4. Graphen erstellen ---
if st.button("Diagramme aktualisieren 🔄", type="primary"):
    
    # Daten vorbereiten
    zeiten = edited_df["Zeit [min]"]
    pegel = edited_df["Wasserstand [m]"]
    
    # Berechnungen
    # A) Förderrate Q (Logik: < pump_end_min)
    q_values = []
    for t in zeiten:
        if t < pump_end_min:
             q_values.append(q_soll)
        else:
             q_values.append(0)
             
    # B) Absenkung s (für das 3. Diagramm)
    # s = Aktueller Pegel - Ruhewasserspiegel
    absenkung_s = pegel - rws

    # --- PLOT START (3 Diagramme untereinander) ---
    # Wir machen das Bild höher (figsize=(10, 15))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15), gridspec_kw={'height_ratios': [2, 1, 2]})
    
    # ---------------------------------------------------------
    # Diagramm 1: Zeit vs. Wasserstand (Klassisch)
    # ---------------------------------------------------------
    ax1.plot(zeiten, pegel, marker='o', markersize=4, linestyle='-', linewidth=2, color='#0077b6', label='Messwerte')
    ax1.axhline(y=rws, color='gray', linestyle='--', linewidth=1, label=f'RWS ({rws}m)')
    ax1.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2, label='Pumpe AUS')
    ax1.set_ylabel('Tiefe unter GOK [m]', fontsize=11)
    ax1.set_title(f'1. Zeit-Absenkungs-Plan', fontsize=13, fontweight='bold')
    ax1.invert_yaxis()
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right')
    # X-Achse ausblenden (teilen sich Achse mit Diagramm 2)
    ax1.tick_params(labelbottom=False)

    # ---------------------------------------------------------
    # Diagramm 2: Zeit vs. Förderleistung Q
    # ---------------------------------------------------------
    ax2.step(zeiten, q_values, where='post', color='#2a9d8f', linewidth=2, label='Förderrate Q')
    ax2.fill_between(zeiten, q_values, step="post", alpha=0.3, color='#2a9d8f')
    ax2.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2)
    ax2.set_ylabel('Q [m³/h]', fontsize=11)
    ax2.set_xlabel('Zeit [min]', fontsize=11)
    ax2.set_title('2. Pumpenleistung über die Zeit', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, q_soll * 1.2)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # X-Achse formatieren (Stunden)
    ticks = np.arange(0, gesamt_dauer_min + 1, 60)
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{int(t/60)}h" for t in ticks])

    # ---------------------------------------------------------
    # Diagramm 3: Förderleistung Q vs. Absenkung s
    # ---------------------------------------------------------
    # X = Q (Förderleistung), Y = s (Absenkung)
    
    # Wir zeichnen den Pfad der Punkte
    ax3.plot(q_values, absenkung_s, marker='o', markersize=5, linestyle='-', linewidth=1.5, color='#e76f51', label='Verlauf (Hysterese)')
    
    # Startpunkt markieren
    ax3.annotate('Start', xy=(q_values[0], absenkung_s[0]), xytext=(q_values[0]+0.2, absenkung_s
