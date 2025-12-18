import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Konfiguration der Seite ---
st.set_page_config(page_title="Bohrprotokoll Generator", page_icon="💧")

st.title("💧 Bohrprotokoll: Abpumpversuch")
st.write("Geben Sie die Messwerte ein, um das Zeit-Absenkungs-Diagramm zu erstellen.")

# --- 1. Eingabe der Stammdaten ---
with st.expander("📝 Stammdaten & Konfiguration", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        projekt_name = st.text_input("Projektname", "BV Müller")
        rws = st.number_input("Ruhewasserspiegel (m u. GOK)", value=2.10, step=0.01)
    with col2:
        pump_end_time = st.number_input("Pumpe AUS nach (min)", value=120, step=10)
        max_tiefe = st.number_input("Max. Tiefe Diagramm (m)", value=5.0, step=0.5)

# --- 2. Dateneingabe (als Tabelle) ---
st.subheader("Messwerte eingeben")
st.info("Tragen Sie hier Zeit (Minuten) und Wasserstand (m) ein.")

# Wir erstellen eine leere Vorlage für die Tabelle
default_data = pd.DataFrame(
    [
        {"Zeit [min]": 0, "Wasserstand [m]": 2.10},
        {"Zeit [min]": 10, "Wasserstand [m]": 3.25},
        {"Zeit [min]": 60, "Wasserstand [m]": 3.42},
        {"Zeit [min]": 120, "Wasserstand [m]": 3.43},
        {"Zeit [min]": 130, "Wasserstand [m]": 2.30},
        {"Zeit [min]": 180, "Wasserstand [m]": 2.12},
    ]
)

# Der Data-Editor erlaubt das Hinzufügen/Löschen von Zeilen direkt in der App
edited_df = st.data_editor(default_data, num_rows="dynamic")

# --- 3. Graph erstellen ---
if st.button("Diagramm erstellen 🚀"):
    
    # Daten sortieren, damit die Linie nicht springt
    df_sorted = edited_df.sort_values(by="Zeit [min]")
    
    zeiten = df_sorted["Zeit [min]"]
    pegel = df_sorted["Wasserstand [m]"]

    # Plot Design (Modern)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Kurve
    ax.plot(zeiten, pegel, marker='o', linestyle='-', linewidth=2.5, color='#0077b6', label='Messdaten')
    
    # Hilfslinien
    ax.axhline(y=rws, color='gray', linestyle='--', label=f'Ruhewasser ({rws} m)')
    ax.axvline(x=pump_end_time, color='#d62828', linestyle=':', linewidth=2, label='Pumpe AUS')

    # Achsen
    ax.set_title(f'Abpumpversuch: {projekt_name}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Zeit [min]')
    ax.set_ylabel('Tiefe unter GOK [m]')
    
    # WICHTIG: Y-Achse umdrehen & Limits setzen
    ax.set_ylim(max_tiefe, 0) # Von Max-Tiefe bis 0 (oben)
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    
    # Anzeigen in Streamlit
    st.pyplot(fig)
    
    # Download Button für das Protokoll
    st.download_button(
        label="Diagramm als Bild speichern 📸",
        data=edited_df.to_csv(index=False).encode('utf-8'),
        file_name='bohrprotokoll_daten.csv',
        mime='text/csv',
    )
