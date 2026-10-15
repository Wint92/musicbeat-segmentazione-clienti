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
GRUPPI = {
    "Famiglie attive": (
        "Piano Family, ascoltano molto e di recente.",
        "Niente sconti: vantaggi esclusivi per mantenerli.",
    ),
    "Famiglie meno attive": (
        "Piano Family, ma pochi accessi: pagano il piano più caro e lo usano poco.",
        "Playlist e suggerimenti di famiglia per aumentare l'uso, prima di una possibile disdetta.",
    ),
    "Attivi con piano base": (
        "Ascoltano molto con un piano Basic o Gratis.",
        "Passaggio a Family con sconto di benvenuto.",
    ),
    "Intermedi e nuovi": (
        "Attività media, in prevalenza Gratis o Basic. Comprende quasi tutti i clienti recenti.",
        "Prova del piano Basic per i Gratis e suggerimenti musicali per aumentare l'ascolto.",
    ),
    "Inattivi": (
        "Pochissimi accessi e molti giorni senza ascoltare.",
        "Campagna di riattivazione; offerta di fidelizzazione per chi paga un abbonamento.",
    ),
}


def carica_risultati():
    """Legge i file prodotti da segmentazione.py. Ritorna None se mancano."""
    if not (FILE_CLIENTI.exists() and FILE_MODELLO.exists()):
        return None
    clienti = pd.read_csv(FILE_CLIENTI, parse_dates=["Data_iscrizione"])
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


def assegna_gruppo(modello, accessi, importo, giorni):
    """Assegna un nuovo cliente a un gruppo, con lo stesso scaler e lo stesso K-means."""
    nuovo = pd.DataFrame([[accessi, importo, giorni]], columns=modello["variabili"])
    X = modello["scaler"].transform(nuovo)
    numero = int(modello["modello"].predict(X)[0])
    return numero, modello["nomi"][numero]
