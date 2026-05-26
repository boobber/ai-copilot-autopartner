import streamlit as st
import pandas as pd
import time

# Konfiguracja strony
st.set_page_config(page_title="AI Sales Copilot", page_icon="🤖", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("katalog_czesci.csv", sep=",", encoding="utf-8")

# Wczytanie danych
df = load_data()

# Nagłówek aplikacji
st.title("🤖 AI Sales Copilot - AutoPartner Max S.A.")
st.markdown("Asystent RAG wspierający proces ofertowania i weryfikację marży.")

# Pasek boczny
st.sidebar.header("Ustawienia Copilota")
st.sidebar.info("Model: Wewnętrzny RAG (Grounded)\n\nTryb: Human-in-the-Loop")

# Pole tekstowe dla zapytania
query = st.text_area(
    "Wklej zapytanie od klienta (mail / SMS / transkrypcja):",
    height=100,
    value="Dzień dobry, potrzebuję komplet hamulców do Octavii 2018, diesel, wersja 2.0. "
          "Klient chce coś rozsądnego cenowo, ale nie najtańsze. Dostawa na dzisiaj."
)

# --- PAMIĘĆ APLIKACJI (SESSION STATE) ---
if "analiza_zrobiona" not in st.session_state:
    st.session_state.analiza_zrobiona = False

if "wartosc_rabatu" not in st.session_state:
    st.session_state.wartosc_rabatu = 10  # Domyślny rabat startowy

# Akcja analizy
if st.button("Analizuj zapytanie i dobierz części", type="primary"):
    st.session_state.analiza_zrobiona = True
    with st.spinner("Analiza NLP zapytania i przeszukiwanie bazy wektorowej..."):
        time.sleep(1.5)

# Sekcja wynikowa
if st.session_state.analiza_zrobiona:
    st.subheader("1. Zidentyfikowane potrzeby (Ekstrakcja NLP)")
    st.write("- **Pojazd:** Skoda Octavia III 2018 2.0 TDI")
    st.write("- **Kategoria:** Hamulce (komplet: przód/tył)")
    st.write("- **Priorytet:** Średnia półka cenowa, natychmiastowa dostępność")

    results = df[
        df["Kategoria"].str.contains("Hamulc", case=False, na=False) &
        df["Pojazd_Kompatybilny"].str.contains("Octavia", case=False, na=False)
    ]

    if not results.empty:
        st.subheader("2. Propozycje AI (Wybierz części do oferty)")
        
        df_wybor = results.copy()
        df_wybor.insert(0, "Wybierz", False)
        
        edytowany_df = st.data_editor(
            df_wybor,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Wybierz": st.column_config.CheckboxColumn("Dodaj do koszyka", default=False)
            },
            disabled=results.columns,
            key="tabela_wyboru"
        )
        
        wybrane_czesci = edytowany_df[edytowany_df["Wybierz"] == True]

        st.divider()

        st.subheader("3. Moduł Ochrony Marży (Dynamic Pricing)")
        
        if wybrane_czesci.empty:
            st.info("👆 Zaznacz co najmniej jedną część z tabeli powyżej, aby zbudować pakiet i przeliczyć ofertę.")
        else:
            cena_katalogowa = wybrane_czesci['Cena_Katalogowa'].sum()
            srednia_min_marza = wybrane_czesci['Min_Marza_Procent'].mean()

            st.write(f"**Liczba wybranych części:** {len(wybrane_czesci)} szt.")
            st.write(f"**Cena wyjściowa pakietu:** {cena_katalogowa:.2f} PLN")

            # --- CSS DLA SUWAKA ---
            aktualny_rabat = st.session_state.wartosc_rabatu
            
            if aktualny_rabat > srednia_min_marza:
                kolor_glowny = "#FF4B4B" # Intensywny czerwony
                kolor_tla = "#FFCCCC"    # Jasnoczerwony dla reszty paska
            else:
                kolor_glowny = "#28A745" # Intensywny zielony
                kolor_tla = "#D4EDDA"    # Jasnozielony dla reszty paska

            st.markdown(f"""
                <style>
                    /* Zmiana tła dla CAŁEGO suwaka (niezaznaczona część) */
                    div[data-testid="stSlider"] div[data-baseweb="slider"] > div {{
                        background: {kolor_tla} !important;
                    }}
                    /* Zmiana koloru aktywnego paska (zaznaczona część) */
                    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {{
                        background: {kolor_glowny} !important;
                    }}
                    /* Kropka suwaka */
                    div[data-testid="stSlider"] div[role="slider"] {{
                        background-color: {kolor_glowny} !important;
                        border-color: {kolor_glowny} !important;
                        box-shadow: 0 0 10px {kolor_glowny}60 !important;
                    }}
                    /* Powiększona liczba nad kropką (tooltip) */
                    div[data-testid="stSlider"] div[role="slider"] > div {{
                        font-size: 24px !important;
                        font-weight: 900 !important;
                        color: {kolor_glowny} !important;
                    }}
                    /* Powiększenie tytułu samego suwaka */
                    div[data-testid="stSlider"] label {{
                        font-size: 20px !important;
                        font-weight: bold !important;
                    }}
                </style>
            """, unsafe_allow_html=True)

            # --- SUWAK ---
            proponowany_rabat = st.slider(
                f"Ustal rabat dla warsztatu ({aktualny_rabat}%)", 
                min_value=0, 
                max_value=30, 
                key="wartosc_rabatu"
            )
            
            # --- PODSUMOWANIE ---
            cena_po_rabacie = cena_katalogowa * (1 - proponowany_rabat / 100)
            st.markdown(f"### Cena ostateczna po rabacie: {cena_po_rabacie:.2f} PLN")

            if proponowany_rabat > srednia_min_marza:
                st.error(
                    f"⚠️ **UWAGA:** Udzielony rabat ({proponowany_rabat}%) jest wyższy niż średnia "
                    f"minimalna marża tego pakietu ({srednia_min_marza:.1f}%). Oferta wymaga akceptacji kierownika."
                )
            else:
                st.success(
                    f"✅ **Rabat w normie:** {proponowany_rabat}% to bezpieczna wartość. Marża operacyjna jest chroniona."
                )

            st.divider()
            
            # --- ZŁÓŻ ZAMÓWIENIE ---
            if st.button("🛒 Złóż zamówienie", type="primary", use_container_width=True):
                st.success("✅ Zamówienie zostało pomyślnie skompletowane i przesłane do systemu ERP! Generowanie listu przewozowego...")
                st.balloons() # Efekt wizualny potwierdzający akcję

    else:
        st.warning("Brak części spełniających kryteria w bazie danych.")