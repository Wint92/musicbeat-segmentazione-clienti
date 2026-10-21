"""
MusicBeat - Dashboard interattiva (Streamlit).

Mostra i gruppi di clienti trovati da segmentazione.py, il profilo di ciascun gruppo,
i filtri (zona, periodo di iscrizione, categoria) e l'assegnazione di un nuovo cliente.

Uso:  streamlit run dashboard.py
"""
import pandas as pd
import streamlit as st

import logica as lg

st.set_page_config(page_title="MusicBeat: segmentazione clienti", layout="wide")

risultati = lg.carica_risultati()
if risultati is None:
    st.error(
        "Mancano i file dei risultati. Esegui prima, nell'ordine:\n\n"
        "`python genera_dati.py` e poi `python segmentazione.py`."
    )
    st.stop()
clienti, confronto, modello = risultati

st.title("MusicBeat: segmentazione dei clienti")
st.caption(
    "Dati interamente simulati, senza informazioni personali. "
    "I gruppi sono trovati con K-means (apprendimento non supervisionato)."
)

# Messaggio lasciato dalla pagina precedente (per esempio dopo aver aggiunto un cliente)
if "messaggio" in st.session_state:
    st.success(st.session_state.pop("messaggio"))

# ---------- Filtri ----------
tutte_zone = sorted(clienti["Zona"].unique())
tutte_categorie = sorted(clienti["Categoria_preferita"].unique())
data_min = clienti["Data_iscrizione"].min().date()
data_max = clienti["Data_iscrizione"].max().date()

st.subheader("Filtri")
f1, f2, f3, f4 = st.columns(4)
zona_scelta = f1.selectbox("Zona", ["Tutte"] + tutte_zone)
categoria_scelta = f2.selectbox("Categoria preferita", ["Tutte"] + tutte_categorie)
data_da = f3.date_input("Iscritti dal", value=data_min, min_value=data_min, max_value=data_max)
data_a = f4.date_input("Iscritti fino al", value=data_max, min_value=data_min, max_value=data_max)
if data_da > data_a:
    st.warning("La data iniziale è dopo quella finale.")
    st.stop()

# "Tutte" = nessun filtro: si usano tutte le zone o tutte le categorie
if zona_scelta == "Tutte":
    zone = tutte_zone
else:
    zone = [zona_scelta]
if categoria_scelta == "Tutte":
    categorie = tutte_categorie
else:
    categorie = [categoria_scelta]

filtrati = lg.filtra(clienti, zone, categorie, data_da, data_a)
if filtrati.empty:
    st.warning("Nessun cliente corrisponde ai filtri scelti.")
    st.stop()

# ---------- Numero di clienti ----------
st.write(f"**Clienti selezionati:** {len(filtrati)} su {len(clienti)}")


tab_gruppi, tab_offerte, tab_nuovo, tab_metodo, tab_dati = st.tabs(
    ["Gruppi", "Idee di offerta", "Nuovo cliente", "Come sono stati scelti i gruppi", "Dati"]
)

# ---------- Gruppi: scatter plot e profilo ----------
with tab_gruppi:
    # Assi fissi: giorni dall'ultimo accesso (orizzontale) e accessi negli ultimi 90 giorni (verticale).
    # Si usano i nomi originali delle colonne; le scritte sugli assi sono date con x_label e y_label.
    st.scatter_chart(
        filtrati,
        x="Giorni_ultimo_accesso",
        y="Accessi_90gg",
        color="Nome_gruppo",
        x_label="Giorni dall'ultimo accesso",
        y_label="Accessi negli ultimi 90 giorni",
    )

    st.subheader("Profilo dei gruppi")
    profilo = lg.profilo_gruppi(filtrati)
    st.dataframe(profilo.rename(columns=lg.ETICHETTE))
    st.bar_chart(profilo["Clienti"])

# ---------- Idee di offerta ----------
with tab_offerte:
    st.caption(
        "Ipotesi di marketing basate su dati simulati. Gli sconti sono calcolati sui prezzi di listino "
        "(Basic 10 €/mese, Family 25 €/mese) e andrebbero verificati con una prova su una parte dei clienti (test A/B)."
    )
    ricavi_totali = filtrati["Importo_totale_90gg"].sum()

    # Prima tabella: solo i numeri (poche colonne, si legge senza scorrere)
    righe = []
    for nome in lg.GRUPPI:
        del_gruppo = filtrati[filtrati["Nome_gruppo"] == nome]
        ricavi = int(del_gruppo["Importo_totale_90gg"].sum())
        if ricavi_totali > 0:
            percentuale = round(100 * ricavi / ricavi_totali, 1)
        else:
            percentuale = 0
        righe.append({
            "Gruppo": nome,
            "Clienti": len(del_gruppo),
            "Ricavi 90 gg (€)": ricavi,
            "% dei ricavi": percentuale,
        })
    st.dataframe(pd.DataFrame(righe), hide_index=True)

    # Poi un riquadro per ogni gruppo, con l'offerta: si legge dall'alto in basso
    for nome in lg.GRUPPI:
        descrizione, offerta, obiettivo, indicatore, perche = lg.GRUPPI[nome]
        with st.container(border=True):
            st.markdown(f"**{nome}**")
            st.write(f"**Chi sono:** {descrizione}")
            st.write(f"**Offerta da proporre:** {offerta}")
            st.write(f"**Perché conviene:** {perche}")
            st.write(f"**Obiettivo:** {obiettivo}")
            st.write(f"**Come misurarlo:** {indicatore}")

# ---------- Nuovo cliente ----------
with tab_nuovo:
    st.write(
        "Inserisci i dati di un nuovo cliente. Puoi vedere a quale gruppo appartiene "
        "(\"Trova il gruppo\") oppure aggiungerlo ai clienti (\"Aggiungi ai clienti\"): "
        "in quel caso i totali e i grafici si aggiornano."
    )
    with st.form("nuovo_cliente"):
        a, b = st.columns(2)
        accessi = a.number_input("Accessi negli ultimi 90 giorni", min_value=0, max_value=200, value=20, step=1)
        giorni = a.number_input("Giorni dall'ultimo accesso", min_value=0, max_value=365, value=10, step=1)
        data_iscrizione = a.date_input(
            "Data di iscrizione",
            value=(lg.DATA_RIFERIMENTO - pd.Timedelta(days=100)).date(),
            min_value=(lg.DATA_RIFERIMENTO - pd.Timedelta(days=365)).date(),
            max_value=lg.DATA_RIFERIMENTO.date(),
        )
        piano = b.selectbox("Piano", list(lg.PREZZI_MENSILI))
        zona_nuovo = b.selectbox("Zona", tutte_zone)
        categoria_nuovo = b.selectbox("Categoria preferita", tutte_categorie)
        prova = st.form_submit_button("Trova il gruppo")
        aggiungi = st.form_submit_button("Aggiungi ai clienti")

    if prova or aggiungi:
        giorni_iscritto = (lg.DATA_RIFERIMENTO - pd.Timestamp(data_iscrizione)).days
        if giorni > giorni_iscritto:
            st.error(
                f"L'ultimo accesso non può essere precedente all'iscrizione: "
                f"il cliente è iscritto da {giorni_iscritto} giorni."
            )
        else:
            riga = lg.crea_riga_cliente(
                clienti, modello, zona_nuovo, categoria_nuovo, data_iscrizione, piano, accessi, giorni
            )
            if aggiungi:
                lg.salva_nuovo_cliente(riga)
                st.session_state["messaggio"] = (
                    f"Cliente {riga['ID_cliente']} aggiunto: gruppo «{riga['Nome_gruppo']}». "
                    f"I clienti sono ora {len(clienti) + 1}."
                )
                st.rerun()  # ricarica la pagina, così i totali si aggiornano
            else:
                descrizione, offerta, obiettivo, indicatore, perche = lg.GRUPPI[riga["Nome_gruppo"]]
                st.success(f"Gruppo di appartenenza: **{riga['Nome_gruppo']}**")
                st.write(
                    f"Importo negli ultimi 90 giorni: {riga['Importo_totale_90gg']} € "
                    f"({piano} × {lg.mesi_pagati(data_iscrizione)} mesi, calcolati dalla data di iscrizione)."
                )
                st.write(f"**Chi sono:** {descrizione}")
                st.write(f"**Offerta da proporre:** {offerta}")
                st.write(f"**Obiettivo:** {obiettivo}. **Come misurarlo:** {indicatore}.")
                st.caption("Il cliente non è stato aggiunto. Premi \"Aggiungi ai clienti\" per salvarlo.")

    # Clienti aggiunti: si possono eliminare per tornare ai dati originali
    n_nuovi = int((clienti["Profilo_simulato"] == "Nuovo").sum())
    if n_nuovi > 0:
        st.write(f"Clienti aggiunti finora: {n_nuovi}.")
        if st.button("Elimina i clienti aggiunti"):
            lg.elimina_nuovi_clienti()
            st.session_state["messaggio"] = "Clienti aggiunti eliminati: si torna ai dati originali."
            st.rerun()

# ---------- Metodo ----------
with tab_metodo:
    st.write(
        "Variabili usate: accessi negli ultimi 90 giorni, importo speso negli ultimi 90 giorni, "
        "giorni dall'ultimo accesso, standardizzate (media 0, deviazione standard 1). "
        "Zona, categoria e data di iscrizione non entrano nel clustering."
    )
    if confronto is not None:
        st.dataframe(confronto, hide_index=True)
    immagine = lg.CARTELLA / "grafici" / "gomito_silhouette.png"
    if immagine.exists():
        st.image(str(immagine))

# ---------- Dati ----------
with tab_dati:
    st.dataframe(filtrati, hide_index=True)
    st.download_button(
        "Scarica i clienti filtrati (CSV)",
        filtrati.to_csv(index=False).encode("utf-8"),
        file_name="clienti_filtrati.csv",
        mime="text/csv",
    )
