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

# Dummy-Daten generieren (NEUE LOGIK)
default_pegel = []
pegel_bei_30 = rws # Variable zum Speichern des Werts bei Min 30
# Ab wann beginnen die letzten 3 Werte? (Gesamtdauer - 2 * 15min)
start_letzte_3 = gesamt_dauer_min - 30 

for t in zeit_intervalle:
    # A) PUMP-PHASE
    if t <= pump_end_min:
        if t == 0:
            wert = rws
        elif t <= 30:
            # Bis Minute 30: Berechnung (logarithmische Absenkung)
            wert = rws + (1.5 * np.log10(t + 1) / np.log10(pump_end_min + 1)) 
            # WICHTIG: Wert bei Minute 30 speichern
            if t == 30:
                pegel_bei_30 = wert
        else:
            # Ab Minute 45 bis Ende Pumpen (480): Konstant Wert von Min 30
            wert = pegel_bei_30
            
    # B) WIEDERANSTIEG-PHASE
    else:
        # Sind wir bei den letzten 3 Werten? -> Setze auf RWS
        if t >= start_letzte_3:
            wert = rws
        else:
            # Dazwischen: Linearer Wiederanstieg vom "Pegel 30" zurück zum RWS
            # Zeit seit Pumpen-Ende
            time_recovery = t - pump_end_min
            # Zeit, die für den Anstieg zur Verfügung steht (bis zu den letzten 3 Werten)
            time_window = start_letzte_3 - pump_end_min
            
            if time_window > 0:
                # Faktor 0 bis 1
                factor = time_recovery / time_window
                wert = pegel_bei_30 - (pegel_bei_30 - rws) * factor
            else:
                wert = rws # Fallback falls Fenster zu klein
                
            if wert < rws: wert = rws # Nicht höher als RWS steigen

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
    
    # Formatierung für Zeit-Achse
    ticks = np.arange(0, gesamt_dauer_min + 1, 60)
    tick_labels = [f"{int(t/60)}h" for t in ticks]

    # ---------------------------------------------------------
    # Diagramm 1: Zeit vs. Wasserstand
    # ---------------------------------------------------------
    ax1.plot(zeiten, pegel, marker='o', markersize=4, linestyle='-', linewidth=2, color='#0077b6', label='Messwerte')
    
    ax1.axhline(y=rws, color='gray', linestyle='--', linewidth=1, label=f'RWS ({rws}m)')
    ax1.text(0, rws, f' Ruhewasserspiegel: {rws:.2f} m', color='#555555', 
             fontsize=10, fontweight='bold', verticalalignment='bottom', backgroundcolor='#ffffffaa')

    ax1.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2, label='Pumpe AUS')

    # Tiefster Punkt (Text)
    ax1.plot(time_at_max, max_tiefe, marker='o', color='red', markersize=8)
    ax1.text(
        time_at_max, 
        max_tiefe - 0.15,
        f'Tiefster Punkt:\n{max_tiefe:.2f} m (bei {int(time_at_max)} min)',
        color='red',
        fontsize=10,
        fontweight='bold',
        ha='center', 
        va='bottom',
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8)
    )

    ax1.set_ylabel('Tiefe unter GOK [m]', fontsize=11)
    ax1.set_title(f'1. Zeit-Absenkungs-Plan', fontsize=13, fontweight='bold', pad=35) 
    ax1.invert_yaxis()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # LEGENDE
    ax1.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=3, frameon=False)

    # X-Achse sichtbar machen
    ax1.tick_params(labelbottom=True)
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(tick_labels)

    # ---------------------------------------------------------
    # Diagramm 2: Zeit vs. Förderleistung Q
    # ---------------------------------------------------------
    ax2.step(zeiten, q_values, where='post', color='#2a9d8f', linewidth=2, label='Förderrate Q')
    ax2.fill_between(zeiten, q_values, step="post", alpha=0.3, color='#2a9d8f')
    ax2.axvline(x=pump_end_min, color='#d62828', linestyle='--', linewidth=2)
    ax2.set_ylabel('Q [m³/h]', fontsize=11)
    ax2.set_xlabel('Zeit [Std]', fontsize=11)
    ax2.set_title('2. Pumpenleistung über die Zeit', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, q_soll * 1.2)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    ax2.set_xticks(ticks)
    ax2.set_xticklabels(tick_labels)

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
