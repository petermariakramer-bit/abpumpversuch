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
        # Absenkung (simuliert)
        wert = rws + (1.5 * np.log10(t + 1) / np.log10(pump_end_min + 1)) 
        if t == 0: wert = rws
    else:
        # Wiederanstieg (simuliert)
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
    
    # Berechnungen: Förderrate Q
    q_values = []
    for t in zeiten:
        if t < pump_end_min:
             q_values.append(q_soll)
        else:
             q_values.append(0)

    # --- Maximalen Absenkungspunkt finden ---
    max_tiefe = pegel.max()
    idx_max = pegel.idxmax()
    time_at_max = zeiten[idx_max]

    # --- PLOT START ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 11), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    
    # ---------------------------------------------------------
    # Diagramm 1: Zeit vs. Wasserstand
    # ---------------------------------------------------------
    ax1.plot(zeiten, pegel, marker='o', markersize=4, linestyle='-', linewidth=2, color='#0077b6', label='Messwerte')
    
    # RWS Linie & Beschriftung
    ax1.axhline(y=rws, color='gray', linestyle='--', linewidth=1, label=f'RWS ({rws}m)')
    ax1.text(0, rws, f' Ruhewasserspiegel: {rws:.2f} m', color='#555555', 
             fontsize=10, fontweight='bold', verticalalignment='bottom', backgroundcolor='#ffffffaa')

    # Linie "Pumpe Aus"
    ax1.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2, label='Pumpe AUS')

    # Tiefster Punkt Markierung
    ax1.plot(time_at_max, max_tiefe, marker='o', color='red', markersize=8)
    ax1.annotate(
        f'Tiefster Punkt:\n{max_tiefe:.2f} m (bei {int(time_at_max)} min)',
        xy=(time_at_max, max_tiefe), 
        xytext=(time_at_max - 120, max_tiefe - 0.2), 
        arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=8),
        fontsize=10,
        color='red',
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8)
    )

    ax1.set_ylabel('Tiefe unter GOK [m]', fontsize=11)
    ax1.set_title(f'1. Zeit-Absenkungs-Plan', fontsize=13, fontweight='bold', pad=40) # Mehr Platz oben für Legende
    ax1.invert_yaxis()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # --- ÄNDERUNG: Legende nach oben außerhalb des Plots ---
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=False)

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
    
    # X-Achse formatieren
    ticks = np.arange(0, gesamt_dauer_min + 1, 60)
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{int(t/60)}h" for t in ticks])

    # Layout straffen
    plt.tight_layout()
    st.pyplot(fig)
    
    # CSV Download
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Daten herunterladen 💾",
        data=csv,
        file_name='pumpversuch_daten.csv',
        mime='text/csv',
    )
