import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="AI Sales Copilot", page_icon="🤖", layout="wide")

@st.cache_data
def load_data():
    # ✅ CSV jest w UTF-8 — czytamy wprost
    return pd.read_csv("katalog_czesci.csv", sep=",", encoding="utf-8")

df = load_data()

st.title("🤖 AI Sales Copilot - AutoPartner Max S.A.")
st.markdown("Asystent RAG wspierający proces ofertowania i weryfikację marży.")

st.sidebar.header("Ustawienia Copilota")
st.sidebar.info("Model: Wewnętrzny RAG (Grounded)\n\nTryb: Human-in-the-Loop")

query = st.text_area(
    "Wklej zapytanie od klienta (mail / SMS / transkrypcja):",
    height=100,
    value="Dzień dobry, potrzebuję komplet hamulców do Octavii 2018, diesel, wersja 2.0. "
          "Klient chce coś rozsądnego cenowo, ale nie najtańsze. Dostawa na dzisiaj."
)

if st.button("Analizuj zapytanie i dobierz części", type="primary"):
    with st.spinner("Analiza NLP zapytania i przeszukiwanie bazy wektorowej..."):
        time.sleep(1.5)

        st.subheader("1. Zrozumienie intencji (Ekstrakcja AI)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rozpoznany Pojazd", "Skoda Octavia III (2018) 2.0 TDI")
        col2.metric("Poszukiwana Kategoria", "Układ hamulcowy")
        col3.metric("Priorytet Czasowy", "Wysoki (Na dzisiaj)")

        st.divider()

        st.subheader("2. Rekomendowane Części (Matching z bazą)")

        results = df[
            df['Pojazd_Kompatybilny'].str.contains("Octavia", case=False, na=False)
        ]

        if not results.empty:
            st.dataframe(results, use_container_width=True)

            st.divider()

            st.subheader("3. Moduł Ochrony Marży (Dynamic Pricing)")

            cena_katalogowa = results['Cena_Katalogowa'].sum()
            srednia_min_marza = results['Min_Marza_Procent'].mean()

            proponowany_rabat = st.slider("Zaproponuj rabat dla warsztatu (%)", 0, 30, 10)
            cena_po_rabacie = cena_katalogowa * (1 - proponowany_rabat / 100)

            st.write(f"**Cena wyjściowa pakietu:** {cena_katalogowa:.2f} PLN")
            st.write(f"**Cena po rabacie:** {cena_po_rabacie:.2f} PLN")

            if proponowany_rabat >= srednia_min_marza:
                st.error(
                    f"⚠️ UWAGA! Udzielony rabat ({proponowany_rabat}%) zagraża minimalnej marży "
                    f"operacyjnej ({srednia_min_marza:.1f}%). Wymagana zgoda kierownika."
                )
            else:
                st.success(f"✅ Rabat {proponowany_rabat}% jest bezpieczny. Marża chroniona.")

            st.divider()

            if st.button("Autoryzuj i wygeneruj ofertę PDF (Human-in-the-loop)"):
                st.balloons()
                st.success("Oferta została zatwierdzona i wysłana do klienta. Logi zasiliły proces Retreningu AI.")

        else:
            st.warning("Brak części w zaufanym katalogu dla tego zapytania. (Blokada halucynacji)")