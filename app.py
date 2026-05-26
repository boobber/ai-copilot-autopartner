import streamlit as st
import pandas as pd
import time

# Konfiguracja strony
st.set_page_config(page_title="AI Sales Copilot", page_icon="🤖", layout="wide")

@st.cache_data
def load_data():
    # Odczyt pliku CSV z jawnym kodowaniem utf-8 dla polskich znaków
    return pd.read_csv("katalog_czesci.csv", sep=",", encoding="utf-8")

# Wczytanie danych
df = load_data()

# Nagłówek aplikacji
st.title("🤖 AI Sales Copilot - AutoPartner Max S.A.")
st.markdown("Asystent RAG wspierający proces ofertowania i weryfikację marży.")

# Pasek boczny (Sidebar)
st.sidebar.header("Ustawienia Copilota")
st.sidebar.info("Model: Wewnętrzny RAG (Grounded)\n\nTryb: Human-in-the-Loop")

# Pole tekstowe dla zapytania od klienta
query = st.text_area(
    "Wklej zapytanie od klienta (mail / SMS / transkrypcja):",
    height=100,
    value="Dzień dobry, potrzebuję komplet hamulców do Octavii 2018, diesel, wersja 2.0. "
          "Klient chce coś rozsądnego cenowo, ale nie najtańsze. Dostawa na dzisiaj."
)

# --- INICJALIZACJA PAMIĘCI APLIKACJI (SESSION STATE) ---
if "analiza_zrobiona" not in st.session_state:
    st.session_state.analiza_zrobiona = False

# Główna akcja po kliknięciu przycisku
if st.button("Analizuj zapytanie i dobierz części", type="primary"):
    # Zapisujemy w pamięci, że analiza została uruchomiona
    st.session_state.analiza_zrobiona = True
    with st.spinner("Analiza NLP zapytania i przeszukiwanie bazy wektorowej..."):
        time.sleep(1.5) # Symulacja działania modelu

# Uruchamiamy resztę kodu na podstawie zapisanej pamięci, a nie samego kliknięcia przycisku
if st.session_state.analiza_zrobiona:
    st.subheader("1. Zidentyfikowane potrzeby (Ekstrakcja NLP)")
    st.write("- **Pojazd:** Skoda Octavia III 2018 2.0 TDI")
    st.write("- **Kategoria:** Hamulce (komplet: przód/tył)")
    st.write("- **Priorytet:** Średnia półka cenowa, natychmiastowa dostępność")

    # Symulowane wyszukiwanie w bazie (filtracja DataFrame dla fraz "Hamulc" i "Octavia")
    results = df[
        df["Kategoria"].str.contains("Hamulc", case=False, na=False) &
        df["Pojazd_Kompatybilny"].str.contains("Octavia", case=False, na=False)
    ]

    if not results.empty:
        st.subheader("2. Propozycje AI (Wybierz części do oferty)")
        
        # Przygotowanie danych do interaktywnej tabeli
        df_wybor = results.copy()
        df_wybor.insert(0, "Wybierz", False)
        
        # Interaktywna tabela
        edytowany_df = st.data_editor(
            df_wybor,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Wybierz": st.column_config.CheckboxColumn(
                    "Dodaj do koszyka", default=False
                )
            },
            disabled=results.columns, # Zablokowanie edycji oryginalnych kolumn z bazy
            key="tabela_wyboru" # Unikalny klucz dla zachowania stanu tabeli
        )
        
        # Filtrujemy tylko zaznaczone części przez sprzedawcę
        wybrane_czesci = edytowany_df[edytowany_df["Wybierz"] == True]

        st.divider()

        st.subheader("3. Moduł Ochrony Marży (Dynamic Pricing)")
        
        # Sprawdzenie, czy cokolwiek zostało dodane do koszyka
        if wybrane_czesci.empty:
            st.info("👆 Zaznacz co najmniej jedną część z tabeli powyżej, aby zbudować pakiet i przeliczyć ofertę.")
        else:
            # Obliczenia bazujące tylko na wybranych pozycjach
            cena_katalogowa = wybrane_czesci['Cena_Katalogowa'].sum()
            srednia_min_marza = wybrane_czesci['Min_Marza_Procent'].mean()

            st.write(f"**Liczba wybranych części:** {len(wybrane_czesci)} szt.")
            st.write(f"**Cena wyjściowa pakietu:** {cena_katalogowa:.2f} PLN")

            # Interaktywny suwak do wyboru rabatu
            proponowany_rabat = st.slider("Ustal rabat dla warsztatu (%)", 0, 30, 10)
            
            # Przeliczenie ceny ostatecznej
            cena_po_rabacie = cena_katalogowa * (1 - proponowany_rabat / 100)

            st.markdown(f"### Cena ostateczna po rabacie: {cena_po_rabacie:.2f} PLN")

            # Weryfikacja poziomu rabatu względem średniej minimalnej marży koszyka
            if proponowany_rabat > srednia_min_marza:
                st.error(
                    f"⚠️ **UWAGA:** Udzielony rabat ({proponowany_rabat}%) jest wyższy niż średnia "
                    f"minimalna marża tego pakietu ({srednia_min_marza:.1f}%). Oferta wymaga akceptacji kierownika."
                )
            else:
                st.success(
                    f"✅ **Rabat w normie:** {proponowany_rabat}% to bezpieczna wartość. Marża operacyjna jest chroniona."
                )
    else:
        st.warning("Brak części spełniających kryteria w bazie danych.")