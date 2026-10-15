"""
MusicBeat - Generatore di dati inventati.

Crea dati/clienti.csv: una riga per cliente, nessun dato personale.
Stesso seed = stessi dati, a ogni esecuzione.

Uso:  python genera_dati.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DATA_RIFERIMENTO = pd.Timestamp("2026-10-01")  # "oggi" per il dataset simulato
FILE_USCITA = Path(__file__).parent / "dati" / "clienti.csv"

PREZZI_MENSILI = {"Gratis": 0, "Basic": 10, "Family": 25}
ZONE = ["Nord", "Centro", "Sud", "Isole"]
P_ZONE = [0.40, 0.25, 0.25, 0.10]
PIANI = ["Gratis", "Basic", "Family"]
CATEGORIE = ["Musica", "Podcast", "Audiolibri"]

# Un profilo = un tipo di cliente.
#   giorni_iscritto, giorni_ultimo: (minimo, massimo escluso)
#   accessi: (media, deviazione standard)
PROFILI = {
    "Assiduo": dict(
        n=100, giorni_iscritto=(120, 366), p_piano=[0.10, 0.60, 0.30],
        accessi=(55, 10), giorni_ultimo=(0, 7), p_categoria=[0.60, 0.25, 0.15],
    ),
    "Inattivo": dict(
        n=110, giorni_iscritto=(150, 366), p_piano=[0.50, 0.40, 0.10],
        accessi=(4, 2), giorni_ultimo=(40, 121), p_categoria=[0.40, 0.30, 0.30],
    ),
    "Occasionale": dict(
        n=150, giorni_iscritto=(90, 366), p_piano=[0.30, 0.55, 0.15],
        accessi=(18, 6), giorni_ultimo=(5, 31), p_categoria=[0.40, 0.40, 0.20],
    ),
    "Recente": dict(
        n=90, giorni_iscritto=(1, 46), p_piano=[0.50, 0.40, 0.10],
        accessi=(6, 3), giorni_ultimo=(0, 11), p_categoria=[0.45, 0.35, 0.20],
    ),
}


def genera_profilo(rng, nome, p):
    n = p["n"]  # quanti clienti creare per questo profilo

    # Giorni di iscrizione: un numero intero casuale tra minimo e massimo
    minimo, massimo = p["giorni_iscritto"]
    giorni_iscritto = rng.integers(minimo, massimo, n)

    # Zona e piano: scelti a caso, con le probabilità indicate
    zona = rng.choice(ZONE, n, p=P_ZONE)
    piano = rng.choice(PIANI, n, p=p["p_piano"])

    # Accessi: numeri casuali attorno a una media (distribuzione "a campana")
    media, dev_standard = p["accessi"]
    accessi = rng.normal(media, dev_standard, n)
    accessi = np.clip(accessi, 0, None)  # niente valori negativi: il minimo è 0
    accessi = accessi.round().astype(int)  # arrotondati a numeri interi

    # Giorni dall'ultimo accesso: un numero intero casuale tra minimo e massimo
    minimo, massimo = p["giorni_ultimo"]
    giorni_ultimo = rng.integers(minimo, massimo, n)
    # Coerenza: l'ultimo accesso non può precedere l'iscrizione
    giorni_ultimo = np.minimum(giorni_ultimo, giorni_iscritto)

    categoria = rng.choice(CATEGORIE, n, p=p["p_categoria"])

    # Data di iscrizione = data di riferimento meno i giorni di iscrizione
    data_iscrizione = DATA_RIFERIMENTO - pd.to_timedelta(giorni_iscritto, unit="D")

    df = pd.DataFrame({
        "Zona": zona,
        "Data_iscrizione": data_iscrizione,
        "Piano": piano,
        "Accessi_90gg": accessi,
        "Giorni_ultimo_accesso": giorni_ultimo,
        "Categoria_preferita": categoria,
    })

    # Importo = prezzo del piano x mesi pagati negli ultimi 90 giorni (max 3)
    mesi_pagati = np.minimum(3, np.ceil(giorni_iscritto / 30)).astype(int)
    df["Importo_totale_90gg"] = df["Piano"].map(PREZZI_MENSILI) * mesi_pagati
    df["Profilo_simulato"] = nome  # solo per controllo: NON usato dal clustering
    return df


def inserisci_valori_mancanti(df, quanti=12):
    """Svuota pochi valori, per esercitare la pulizia dei dati."""
    rng_buchi = np.random.default_rng(SEED)
    df = df.copy()
    for colonna in ["Accessi_90gg", "Giorni_ultimo_accesso"]:
        df[colonna] = df[colonna].astype(float)
        righe = rng_buchi.choice(df.index, quanti, replace=False)
        df.loc[righe, colonna] = np.nan
    return df


def main():
    rng = np.random.default_rng(SEED)
    # Una tabella per ogni profilo, poi le mettiamo una sotto l'altra
    pezzi = []
    for nome, p in PROFILI.items():
        pezzi.append(genera_profilo(rng, nome, p))
    clienti = pd.concat(pezzi, ignore_index=True)

    # Mescoliamo le righe, altrimenti i clienti resterebbero ordinati per profilo
    clienti = clienti.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Codice anonimo: C0001, C0002, ...
    codici = []
    for numero in range(1, len(clienti) + 1):
        codici.append("C" + str(numero).zfill(4))
    clienti.insert(0, "ID_cliente", codici)

    clienti = inserisci_valori_mancanti(clienti)

    FILE_USCITA.parent.mkdir(exist_ok=True)
    clienti.to_csv(FILE_USCITA, index=False)
    print(f"Creati {len(clienti)} clienti -> {FILE_USCITA}")
    print("Valori mancanti inseriti:")
    print(clienti[["Accessi_90gg", "Giorni_ultimo_accesso"]].isna().sum())


if __name__ == "__main__":
    main()
