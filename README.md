# MusicBeat — Segmentazione automatica dei clienti

Prototipo di segmentazione dei clienti di MusicBeat, un servizio di musica in streaming
(azienda **inventata**). Partendo da dati simulati, un algoritmo di apprendimento non
supervisionato (K-means) individua gruppi di clienti con comportamenti simili, e una
dashboard interattiva permette di esplorarli.

> Tutti i dati sono generati per l'occasione. Non contengono informazioni personali:
> ogni cliente è identificato da un codice anonimo (C0001, C0002, ...).

## Prova la dashboard online

Per usare la dashboard **non serve installare nulla**: basta aprire questo link.



***https://musicbeat-segmentazione-clienti-nxr3hpljamwohpmvqxfyeq.streamlit.app/***



Aprendo `dashboard.py` qui su GitHub si vede soltanto il codice; la dashboard funziona dal
link qui sopra. Se compare il messaggio "This app has gone to sleep", cliccare sul pulsante
per riattivarla (ci vuole circa un minuto).

In alternativa si può eseguire sul proprio computer, come descritto in "Come eseguirlo".

## Contenuto

|File|A cosa serve|
|-|-|
|`genera\_dati.py`|Genera 450 clienti simulati e li salva in `dati/clienti.csv`|
|`segmentazione.py`|Pulisce i dati, standardizza, sceglie k, esegue K-means e salva i risultati|
|`logica.py`|Funzioni usate dalla dashboard (filtri, profili dei gruppi, assegnazione di un nuovo cliente)|
|`dashboard.py`|Dashboard interattiva (Streamlit)|
|`dati/clienti.csv`|Dati simulati, una riga per cliente|
|`risultati/clienti\_segmentati.csv`|Dati con il gruppo assegnato a ogni cliente|
|`risultati/profilo\_gruppi.csv`|Valori medi e numerosità di ciascun gruppo|
|`risultati/confronto\_k.csv`|Inertia e silhouette per k da 2 a 8|
|`risultati/modello.joblib`|Scaler e modello K-means salvati (usati dalla dashboard)|
|`risultati/nuovi\_clienti.csv`|Creato solo se si aggiungono clienti dalla dashboard (non è incluso nel progetto)|
|`grafici/`|Grafici del metodo del gomito, della silhouette e dei gruppi|

## Come eseguirlo

Serve Python 3.10 o successivo.

```bash
pip install -r requirements.txt

python genera\_dati.py        # 1. crea dati/clienti.csv
python segmentazione.py      # 2. crea i risultati in risultati/ e i grafici in grafici/
streamlit run dashboard.py   # 3. apre la dashboard nel browser
```

I tre passaggi vanno eseguiti in quest'ordine. Il risultato è **riproducibile**: con gli stessi
parametri si ottengono sempre gli stessi dati e gli stessi gruppi.

## I dati simulati

Una riga per cliente, con queste colonne:

|Colonna|Significato|
|-|-|
|`ID\_cliente`|Codice anonimo|
|`Zona`|Nord, Centro, Sud, Isole|
|`Data\_iscrizione`|Data di iscrizione al servizio|
|`Piano`|Gratis (0 €/mese), Basic (10 €/mese), Family (25 €/mese)|
|`Accessi\_90gg`|Numero di accessi al servizio negli ultimi 90 giorni|
|`Giorni\_ultimo\_accesso`|Giorni trascorsi dall'ultimo accesso|
|`Categoria\_preferita`|Musica, Podcast, Audiolibri|
|`Importo\_totale\_90gg`|Prezzo mensile del piano × mesi pagati negli ultimi 90 giorni (massimo 3)|
|`Profilo\_simulato`|Tipo di cliente usato per generare i dati. **Non è usato dal clustering**: serve solo a controllare i risultati|

I clienti sono generati a partire da quattro profili (assiduo 100, occasionale 150,
inattivo 110, recente 90). Un cliente iscritto da meno di tre mesi ha pagato meno mesi,
e l'ultimo accesso non può essere precedente all'iscrizione.
Nel file sono stati inseriti di proposito 12 valori mancanti in `Accessi\_90gg` e 12 in
`Giorni\_ultimo\_accesso`, per mostrare la fase di pulizia.

## Metodo

1. **Pulizia**: i valori mancanti sono sostituiti con la mediana della colonna (12 accessi, 10 giorni).
2. **Variabili usate**: `Accessi\_90gg`, `Importo\_totale\_90gg`, `Giorni\_ultimo\_accesso`.
Zona, categoria e data di iscrizione non entrano nel clustering e servono per i filtri.
3. **Normalizzazione**: standardizzazione (media 0, deviazione standard 1) con `StandardScaler`,
perché K-means si basa sulle distanze.
4. **Scelta di k**: confronto di k da 2 a 8 con il metodo del gomito (inertia) e l'indice di
silhouette. Tra 3 e 5 gruppi si sceglie il k con la silhouette più alta.
5. **K-means**: `KMeans(n\_clusters=k, n\_init=10, random\_state=42)`.

Parametri: seed 42 in tutti gli script; `n\_init=10`; intervallo di k richiesto 3-5.

## Risultati

Con questi parametri la silhouette più alta è per k = 5 (0,532, contro 0,509 per k = 4 e 0,459 per k = 3).

|Gruppo|Clienti|Accessi (90 gg)|Importo (90 gg)|Giorni dall'ultimo accesso|
|-|-|-|-|-|
|Intermedi e nuovi|219|13,0|15,7 €|12,3|
|Inattivi|95|4,6|11,5 €|78,5|
|Attivi con piano base|60|57,2|27,0 €|3,4|
|Famiglie meno attive|42|13,6|72,6 €|25,9|
|Famiglie attive|34|53,8|75,0 €|3,6|

I nomi dei gruppi sono assegnati da `segmentazione.py` con regole basate sulle medie
(per k = 5). Le idee di offerta per ciascun gruppo sono nella dashboard (scheda "Idee di offerta").

## La dashboard

* **Filtri** (barra laterale): zona, periodo di iscrizione, categoria preferita.
* **Gruppi**: grafico a dispersione (assi selezionabili), profilo e numerosità di ciascun gruppo.
* **Idee di offerta**: interpretazione di marketing di ogni gruppo.
* **Nuovo cliente**: inserendo accessi, giorni dall'ultimo accesso, data di iscrizione, piano,
zona e categoria, "Trova il gruppo" mostra il gruppo di appartenenza, mentre
"Aggiungi ai clienti" salva il cliente in `risultati/nuovi\_clienti.csv` e aggiorna totali e grafici
(da 450 a 451 clienti). "Elimina i clienti aggiunti" riporta ai 450 originali.
I mesi pagati sono calcolati dalla data di iscrizione.
* **Come sono stati scelti i gruppi**: tabella e grafici di gomito e silhouette.
* **Dati**: tabella filtrata, scaricabile in CSV.

## Limiti e possibili miglioramenti

* I dati sono simulati: le relazioni tra comportamento e piano sono ipotesi inserite nel generatore, non risultati su clienti reali. Con dati reali i gruppi sarebbero meno netti.
* L'importo dipende dal piano e assume pochi valori distinti: è una variabile meno ricca di una spesa continua.
* I clienti recenti non formano un gruppo a sé, perché nessuna variabile usata ne descrive l'anzianità. Si potrebbero aggiungere i giorni dall'iscrizione.
* Le variabili categoriche (zona, categoria) non sono usate nel clustering.
* Con 450 clienti, k = 4 e k = 5 hanno silhouette vicine (0,509 e 0,532): la scelta di k è una convenzione ragionevole, non una verità.
* I clienti aggiunti dalla dashboard sono assegnati a un gruppo con il modello già addestrato, ma non lo modificano: per includerli nel clustering va rieseguita la segmentazione.
* Si potrebbero provare altri algoritmi di raggruppamento e aggiornare la segmentazione periodicamente.
* I risultati numerici possono variare leggermente con versioni molto diverse delle librerie.

