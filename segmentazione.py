"""
MusicBeat - Segmentazione dei clienti con K-means.

Legge dati/clienti.csv e produce, nella cartella risultati/:
  clienti_segmentati.csv, profilo_gruppi.csv, confronto_k.csv, modello.joblib
e grafici/gomito_silhouette.png

Uso:  python segmentazione.py
"""
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

SEED = 42
CARTELLA = Path(__file__).parent
FILE_DATI = CARTELLA / "dati" / "clienti.csv"
VARIABILI = ["Accessi_90gg", "Importo_totale_90gg", "Giorni_ultimo_accesso"]
K_MIN, K_MAX = 3, 5  # intervallo richiesto dalla traccia


def pulisci(df):
    """Pulizia di base: duplicati e valori mancanti (sostituiti con la mediana)."""
    df = df.drop_duplicates(subset="ID_cliente").copy()
    for colonna in VARIABILI:
        mancanti = df[colonna].isna().sum()
        if mancanti:
            mediana = round(df[colonna].median())
            df[colonna] = df[colonna].fillna(mediana)
            print(f"{colonna}: {mancanti} valori mancanti -> mediana {mediana}")
    return df


def confronta_k(X):
    """Inertia (gomito) e silhouette per k da 2 a 8."""
    righe = []
    for k in range(2, 9):
        modello = KMeans(n_clusters=k, n_init=10, random_state=SEED)
        etichette = modello.fit_predict(X)
        righe.append({
            "k": k,
            "inertia": round(modello.inertia_, 1),
            "silhouette": round(silhouette_score(X, etichette), 3),
        })
    return pd.DataFrame(righe)


def grafico_k(confronto, percorso):
    fig, assi = plt.subplots(1, 2, figsize=(10, 4))
    assi[0].plot(confronto["k"], confronto["inertia"], marker="o")
    assi[0].set(title="Metodo del gomito", xlabel="Numero di gruppi (k)", ylabel="Inertia")
    assi[1].plot(confronto["k"], confronto["silhouette"], marker="o")
    assi[1].set(title="Indice di silhouette", xlabel="Numero di gruppi (k)", ylabel="Silhouette")
    plt.tight_layout()
    percorso.parent.mkdir(exist_ok=True)
    fig.savefig(percorso, dpi=120)
    plt.close(fig)


def grafico_dispersione(clienti, percorso):
    """Scatter plot: giorni dall'ultimo accesso contro accessi, un colore per gruppo."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for nome, dati in clienti.groupby("Nome_gruppo"):
        ax.scatter(dati["Giorni_ultimo_accesso"], dati["Accessi_90gg"],
                   label=nome, alpha=0.7)
    ax.set(title="Gruppi di clienti MusicBeat",
           xlabel="Giorni dall'ultimo accesso",
           ylabel="Accessi negli ultimi 90 giorni")
    ax.legend()
    percorso.parent.mkdir(exist_ok=True)
    fig.savefig(percorso, dpi=120)
    plt.close(fig)


def nomina_gruppi(medie):
    """Assegna un nome a ogni gruppo in base alle medie (valido per k = 5)."""
    nomi = {}
    resto = list(medie.index)

    # 1) il gruppo con più giorni dall'ultimo accesso sono gli Inattivi
    g = medie.loc[resto, "Giorni_ultimo_accesso"].idxmax()
    nomi[g] = "Inattivi"
    resto.remove(g)

    # 2) i due gruppi con importo più alto sono le Famiglie (piano Family):
    #    quello con più accessi è "attivo", l'altro "meno attivo"
    due_famiglie = medie.loc[resto, "Importo_totale_90gg"].nlargest(2).index.tolist()
    primo, secondo = due_famiglie
    if medie.loc[primo, "Accessi_90gg"] >= medie.loc[secondo, "Accessi_90gg"]:
        nomi[primo] = "Famiglie attive"
        nomi[secondo] = "Famiglie meno attive"
    else:
        nomi[secondo] = "Famiglie attive"
        nomi[primo] = "Famiglie meno attive"
    resto.remove(primo)
    resto.remove(secondo)

    # 3) dei due gruppi rimasti, quello con più accessi è "Attivi con piano base"
    primo, secondo = resto
    if medie.loc[primo, "Accessi_90gg"] >= medie.loc[secondo, "Accessi_90gg"]:
        nomi[primo] = "Attivi con piano base"
        nomi[secondo] = "Intermedi e nuovi"
    else:
        nomi[secondo] = "Attivi con piano base"
        nomi[primo] = "Intermedi e nuovi"
    return nomi


def main():
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    clienti = pulisci(pd.read_csv(FILE_DATI, parse_dates=["Data_iscrizione"]))

    scaler = StandardScaler()
    X = scaler.fit_transform(clienti[VARIABILI])

    confronto = confronta_k(X)
    print("\nConfronto tra numeri di gruppi:")
    print(confronto.to_string(index=False))

    candidati = confronto[confronto["k"].between(K_MIN, K_MAX)]
    riga_migliore = candidati["silhouette"].idxmax()  # riga con la silhouette più alta
    k_scelto = int(candidati.loc[riga_migliore, "k"])
    print(f"\nk scelto (silhouette massima tra {K_MIN} e {K_MAX}): {k_scelto}")

    modello = KMeans(n_clusters=k_scelto, n_init=10, random_state=SEED)
    clienti["Gruppo"] = modello.fit_predict(X)

    medie = clienti.groupby("Gruppo")[VARIABILI].mean()
    # I nomi sono assegnati con regole pensate per k = 5; con altri k restano numeri.
    if k_scelto == 5:
        nomi = nomina_gruppi(medie)
    else:
        nomi = {}
        for g in medie.index:
            nomi[g] = "Gruppo " + str(g)
    clienti["Nome_gruppo"] = clienti["Gruppo"].map(nomi)

    profilo = clienti.groupby("Nome_gruppo")[VARIABILI].mean().round(1)
    profilo["Clienti"] = clienti["Nome_gruppo"].value_counts()
    print("\nProfilo dei gruppi:")
    print(profilo)

    print("\nControllo con il profilo simulato (non usato dal clustering):")
    print(pd.crosstab(clienti["Profilo_simulato"], clienti["Nome_gruppo"]))

    uscita = CARTELLA / "risultati"
    uscita.mkdir(exist_ok=True)
    clienti.to_csv(uscita / "clienti_segmentati.csv", index=False)
    profilo.to_csv(uscita / "profilo_gruppi.csv")
    confronto.to_csv(uscita / "confronto_k.csv", index=False)
    joblib.dump({"scaler": scaler, "modello": modello, "nomi": nomi, "variabili": VARIABILI},
                uscita / "modello.joblib")
    grafico_k(confronto, CARTELLA / "grafici" / "gomito_silhouette.png")
    grafico_dispersione(clienti, CARTELLA / "grafici" / "gruppi_dispersione.png")
    print(f"\nFile salvati in {uscita}")


if __name__ == "__main__":
    main()
