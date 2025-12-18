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
    
    # Umrechnung in Minuten für die Berechnungen
    pump_end_min = pump_dauer_h * 60
    gesamt_dauer_min = gesamt_dauer_h * 60

# --- 2. Automatische Generierung der Zeit-Intervalle ---
# Wir erzeugen eine Liste von 0 bis zur Gesamtdauer in 15-Minuten-Schritten
zeit_intervalle = list(range(0, gesamt_dauer_min + 1, 15))

# Wir erstellen Dummy-Daten für den Wasserstand, damit die Tabelle nicht leer ist
# (Simulierter Verlauf: Absenkung bis Stunde 8, dann Wiederanstieg)
default_pegel = []
for t in zeit_intervalle:
    if t <= pump_end_min:
        # Während des Pumpens: Wasserstand sinkt langsam (Logarithmisch angenähert)
        wert = rws + (1.5 * np.log10(t + 1) / np.log10(pump_end_min + 1)) 
        if t == 0: wert = rws
    else:
        # Wiederanstieg: Wasserstand geht zurück Richtung RWS
        time_recovery = t - pump_end_min
        wert = default_pegel[-1] - (default_pegel[-1] - rws) * (time_recovery / 120)
        if wert < rws: wert = rws
    
    default_pegel.append(round(wert, 2))

# DataFrame erstellen
df_template = pd.DataFrame({
    "Zeit [min]": zeit_intervalle,
    "Wasserstand [m]": default_pegel
})

# --- 3. Dateneingabe ---
st.subheader("📝 Messwerte eingeben")
st.info(f"Die Tabelle wurde automatisch für {gesamt_dauer_h} Stunden im 15-Minuten-Takt vorbefüllt. Sie können die Wasserstände direkt bearbeiten.")

# Editor für die Daten
edited_df = st.data_editor(
    df_template, 
    height=300, 
    use_container_width=True,
    num_rows="dynamic"
)

# --- 4. Graphen erstellen ---
if st.button("Diagramme aktualisieren 🔄", type="primary"):
    
    # Daten auslesen
    zeiten = edited_df["Zeit [min]"]
    pegel = edited_df["Wasserstand [m]"]
    
    # Förderleistung Q berechnen
    # KORREKTUR: Wir prüfen "strictly less" (<). 
    # Wenn wir bei Minute 480 sind, muss der Wert für das Intervall 480-495 schon 0 sein.
    q_values = []
    for t in zeiten:
        if t < pump_end_min:  
             q_values.append(q_soll) # Pumpe läuft (z.B. bis Minute 479)
        else:
             q_values.append(0)      # Ab Minute 480 (8h) ist sie aus
            
    # --- PLOT START ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    
    # --- Diagramm 1: Wasserstand (Absenkung) ---
    ax1.plot(zeiten, pegel, marker='o', markersize=4, linestyle='-', linewidth=2, color='#0077b6', label='Messwerte')
    
    # Hilfslinien Diagramm 1
    ax1.axhline(y=rws, color='gray', linestyle='--', linewidth=1, label=f'Ruhewasserspiegel ({rws}m)')
    ax1.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2, label=f'Pumpe AUS ({pump_dauer_h}h)')
    
    ax1.set_ylabel('Tiefe unter GOK [m]', fontsize=12)
    ax1.set_title(f'Absenkung & Wiederanstieg: {projekt_name}', fontsize=14, fontweight='bold')
    ax1.invert_yaxis() # Tiefe nach unten
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right')

    # --- Diagramm 2: Förderleistung (Q) ---
    # Wir nutzen "step" mit 'post'. Das bedeutet: Der Wert bei t=0 gilt für das Intervall 0-15 min.
    ax2.step(zeiten, q_values, where='post', color='#2a9d8f', linewidth=2, label='Förderrate Q')
    
    # Fläche füllen (auch mit step='post' damit es passt)
    ax2.fill_between(zeiten, q_values, step="post", alpha=0.3, color='#2a9d8f')
    
    # Hilfslinie
    ax2.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2)
    
    ax2.set_ylabel('Förderleistung Q [m³/h]', fontsize=12)
    ax2.set_xlabel('Zeit [min]', fontsize=12)
    ax2.set_title('Förderleistung über die Zeit', fontsize=12, fontweight='bold')
    
    # Y-Achse etwas höher setzen für gute Optik
    ax2.set_ylim(0, q_soll * 1.2) 
    
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right')

    # X-Achsen-Ticks stündlich
    ticks = np.arange(0, gesamt_dauer_min + 1, 60)
    ax2.set_xticks(ticks)
    # Damit 1h, 2h usw. als Beschriftung steht (optional, sonst bleiben es Minuten)
    ax2.set_xticklabels([f"{int(t/60)}h" for t in ticks])
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Download Button
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Daten als CSV herunterladen 💾",
        data=csv,
        file_name='pumpversuch_daten.csv',
        mime='text/csv',
    )
