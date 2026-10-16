"""
MusicBeat - Funzioni usate dalla dashboard (senza interfaccia grafica).

Sono tenute in un file separato per poterle controllare anche senza Streamlit.
"""
import math
from pathlib import Path

import joblib
import pandas as pd

CARTELLA = Path(__file__).parent
FILE_CLIENTI = CARTELLA / "risultati" / "clienti_segmentati.csv"
# I clienti aggiunti dalla dashboard sono salvati qui, a parte: i 450 dati originali non cambiano.
FILE_NUOVI = CARTELLA / "risultati" / "nuovi_clienti.csv"
DATA_RIFERIMENTO = pd.Timestamp("2026-10-01")  # "oggi" per il dataset simulato
FILE_PROFILO = CARTELLA / "risultati" / "profilo_gruppi.csv"
FILE_CONFRONTO = CARTELLA / "risultati" / "confronto_k.csv"
FILE_MODELLO = CARTELLA / "risultati" / "modello.joblib"

VARIABILI = ["Accessi_90gg", "Importo_totale_90gg", "Giorni_ultimo_accesso"]
ETICHETTE = {
    "Accessi_90gg": "Accessi negli ultimi 90 giorni",
    "Importo_totale_90gg": "Importo speso negli ultimi 90 giorni (€)",
    "Giorni_ultimo_accesso": "Giorni dall'ultimo accesso",
}
PREZZI_MENSILI = {"Gratis": 0, "Basic": 10, "Family": 25}

# Interpretazione di marketing: ipotesi basate su dati simulati.
# Per ogni gruppo: chi sono, offerta (azione e prezzo), obiettivo, come misurarlo, perché conviene.
# Gli sconti sono calcolati sui prezzi di listino: Basic 10 €/mese, Family 25 €/mese.
GRUPPI = {
    "Famiglie attive": (
        "Piano Family, ascoltano molto e di recente.",
        "Nessuno sconto. Vantaggi esclusivi inclusi nel piano Family a 25 € al mese: accesso anticipato "
        "ai nuovi contenuti e un profilo extra senza costo.",
        "Non perderli",
        "Disdette nel periodo",
        "Pagano già il prezzo pieno e usano molto il servizio: uno sconto ridurrebbe i ricavi senza "
        "bisogno, mentre i vantaggi esclusivi costano poco e aumentano la fedeltà.",
    ),
    "Famiglie meno attive": (
        "Piano Family, ma pochi accessi: pagano il piano più caro e lo usano poco.",
        "Un mese di Family a 20 € invece di 25 € (-20%), insieme a playlist di famiglia e promemoria "
        "di ascolto.",
        "Far usare il piano che pagano",
        "Aumento degli accessi in 30 giorni",
        "Lo sconto costa 5 € a cliente, una volta sola; se il cliente disdice si perdono 25 € al mese.",
    ),
    "Attivi con piano base": (
        "Ascoltano molto con un piano Basic o Gratis.",
        "Passaggio a Family con 2 mesi a 15 € invece di 25 € (-40%), poi 25 € al mese. Per i pochi con "
        "piano Gratis, prima un mese di Basic a 5 €.",
        "Aumentare il ricavo medio",
        "Clienti passati a Family",
        "Anche durante lo sconto il cliente paga 5 € in più al mese rispetto al Basic (15 € contro "
        "10 €); finito lo sconto, 15 € in più.",
    ),
    "Intermedi e nuovi": (
        "Attività media, in prevalenza Gratis o Basic. Comprende quasi tutti i clienti recenti.",
        "Ai clienti Gratis, il primo mese di Basic a 5 € invece di 10 € (-50%), con suggerimenti "
        "musicali sulle categorie preferite. Ai nuovi iscritti, un messaggio di benvenuto con le "
        "playlist più ascoltate.",
        "Convertire i clienti Gratis",
        "Clienti passati da Gratis a Basic",
        "Un cliente Gratis non porta ricavi: ogni passaggio a Basic dà almeno 5 € il primo mese e poi "
        "10 € al mese.",
    ),
    "Inattivi": (
        "Pochissimi accessi e molti giorni senza ascoltare.",
        "Per chi paga il Basic: 3 mesi a 5 € invece di 10 € (-50%), con il messaggio «Ci sei mancato» e "
        "novità scelte per lui. Per chi ha il piano Gratis: solo il messaggio di riattivazione, senza "
        "sconto.",
        "Farli tornare ad ascoltare",
        "Clienti con un nuovo accesso entro 30 giorni",
        "Un Basic che non ascolta rischia di disdire e di far perdere 10 € al mese; lo sconto costa 5 € "
        "al mese per tre mesi. Ai clienti Gratis il messaggio non costa nulla.",
    ),
}


def carica_risultati():
    """Legge i file prodotti da segmentazione.py. Ritorna None se mancano."""
    if not (FILE_CLIENTI.exists() and FILE_MODELLO.exists()):
        return None
    clienti = pd.read_csv(FILE_CLIENTI, parse_dates=["Data_iscrizione"])
    # Se sono stati aggiunti dei clienti dalla dashboard, li mettiamo in fondo alla tabella
    if FILE_NUOVI.exists():
        nuovi = pd.read_csv(FILE_NUOVI, parse_dates=["Data_iscrizione"])
        clienti = pd.concat([clienti, nuovi], ignore_index=True)
    confronto = pd.read_csv(FILE_CONFRONTO) if FILE_CONFRONTO.exists() else None
    modello = joblib.load(FILE_MODELLO)
    return clienti, confronto, modello


def filtra(clienti, zone, categorie, data_da, data_a):
    """Applica i filtri della dashboard: zona, categoria preferita, periodo di iscrizione."""
    filtro = (
        clienti["Zona"].isin(zone)
        & clienti["Categoria_preferita"].isin(categorie)
        & (clienti["Data_iscrizione"] >= pd.Timestamp(data_da))
        & (clienti["Data_iscrizione"] <= pd.Timestamp(data_a))
    )
    return clienti[filtro]


def profilo_gruppi(clienti):
    """Valori medi delle variabili principali e numerosità di ogni gruppo."""
    profilo = clienti.groupby("Nome_gruppo")[VARIABILI].mean().round(1)
    profilo["Clienti"] = clienti["Nome_gruppo"].value_counts()
    profilo["% clienti"] = (100 * profilo["Clienti"] / len(clienti)).round(1)
    return profilo.sort_values("Clienti", ascending=False)


def importo_da_piano(piano, mesi_pagati):
    """Importo negli ultimi 90 giorni: prezzo mensile del piano per i mesi pagati (0-3)."""
    return PREZZI_MENSILI[piano] * mesi_pagati


def mesi_pagati(data_iscrizione):
    """Mesi pagati negli ultimi 90 giorni (da 0 a 3), calcolati dalla data di iscrizione."""
    giorni_iscritto = (DATA_RIFERIMENTO - pd.Timestamp(data_iscrizione)).days
    mesi = math.ceil(giorni_iscritto / 30)  # 45 giorni -> 2 mesi
    return min(3, mesi)


def crea_riga_cliente(clienti, modello, zona, categoria, data_iscrizione, piano, accessi, giorni):
    """Costruisce la riga di un nuovo cliente, con importo e gruppo calcolati."""
    numero = len(clienti) + 1  # il nuovo cliente è il successivo della tabella
    importo = importo_da_piano(piano, mesi_pagati(data_iscrizione))
    gruppo, nome_gruppo = assegna_gruppo(modello, accessi, importo, giorni)
    return {
        "ID_cliente": "C" + str(numero).zfill(4),
        "Zona": zona,
        "Data_iscrizione": pd.Timestamp(data_iscrizione),
        "Piano": piano,
        "Accessi_90gg": accessi,
        "Giorni_ultimo_accesso": giorni,
        "Categoria_preferita": categoria,
        "Importo_totale_90gg": importo,
        "Profilo_simulato": "Nuovo",  # non è un profilo simulato: è un cliente aggiunto a mano
        "Gruppo": gruppo,
        "Nome_gruppo": nome_gruppo,
    }


def salva_nuovo_cliente(riga):
    """Aggiunge il cliente al file dei nuovi clienti (lo crea se non esiste)."""
    tabella = pd.DataFrame([riga])
    tabella.to_csv(FILE_NUOVI, mode="a", header=not FILE_NUOVI.exists(), index=False)


def elimina_nuovi_clienti():
    """Cancella i clienti aggiunti dalla dashboard: si torna ai 450 originali."""
    if FILE_NUOVI.exists():
        FILE_NUOVI.unlink()


def assegna_gruppo(modello, accessi, importo, giorni):
    """Assegna un nuovo cliente a un gruppo, con lo stesso scaler e lo stesso K-means."""
    nuovo = pd.DataFrame([[accessi, importo, giorni]], columns=modello["variabili"])
    X = modello["scaler"].transform(nuovo)
    numero = int(modello["modello"].predict(X)[0])
    return numero, modello["nomi"][numero]
