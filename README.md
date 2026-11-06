# Questlog

Applicazione da terminale per catalogare la propria libreria di videogiochi e tenere traccia di voti e partite: ogni partita ha piattaforma, stato, ore di gioco e date.

> Progetto in sviluppo. Questa è la versione a riga di comando: le prossime fasi aggiungeranno statistiche, grafici e un'interfaccia desktop.

## Funzionalità

- **Aggiunta** di un gioco già iniziato, con voto e prima partita, oppure da giocare, in backlog.
- **Più partite per gioco**: rigiocare un titolo, anche su un'altra piattaforma, aggiunge una partita allo stesso gioco.
- **Visualizzazione** della libreria numerata, con numero di partite, ore totali, voto e un segno ✓ per i giochi completati almeno una volta.
- **Scheda del gioco** con voto, ore totali ed elenco delle partite, da cui si gestiscono partite, titolo, voto ed eliminazione.
- **Ricerca** per titolo, parziale e senza distinzione tra maiuscole e minuscole.
- **Filtro** per stato: trova i giochi con almeno una partita in quello stato, oppure i giochi in backlog.
- **Esportazione e importazione CSV**, per aprire la libreria in Excel o ripristinarla da un backup.
- **Eliminazione** di giochi e partite con richiesta di conferma.
- **Date automatiche** nei cambi di stato.
- **Salvataggio automatico** dopo ogni modifica e caricamento all'avvio.
- **Validazione** di ogni dato inserito: campi vuoti, numeri e date non validi, duplicati.

## Requisiti e avvio

- Python 3.10 o superiore
- Nessuna libreria esterna per usare l'applicazione

```bash
python main.py
```

La libreria viene salvata nel file `game_library.json`, nella cartella del progetto. Il file è escluso dal repository perché contiene dati personali, come l'export `questlog_export.csv`.

### Sviluppo

Per eseguire i test serve un ambiente virtuale con le dipendenze di sviluppo:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

## Regole della libreria

### Giochi e partite

Un gioco ha un titolo, un voto e zero o più partite. Piattaforma, stato, ore e date appartengono alla singola partita, mentre il voto è unico per il gioco.

- Un gioco **senza partite** è in **backlog**: posseduto, mai iniziato.
- Eliminando l'ultima partita, il gioco torna in backlog e perde il voto, dopo conferma.
- Le ore totali del gioco sono la somma delle ore di tutte le partite.
- Lo stesso gioco può avere più partite, anche sulla stessa piattaforma.

### Stati di una partita

| Stato | Significato |
|---|---|
| `playing` | in corso |
| `completed` | completata |
| `dropped` | abbandonata |

`backlog` non è uno stato della partita ma la condizione di un gioco senza partite. Nel filtro per stato compare insieme agli altri tre.

### Ore giocate

| Situazione | Regola |
|---|---|
| Partita `playing` o `dropped` | ore richieste, 0 ammesso |
| Partita `completed` | ore richieste, maggiori di 0 |
| Qualsiasi partita | ore mai negative, valori non numerici rifiutati |

### Voto

- Facoltativo, da 1 a 10, con mezzi punti ammessi (es. `7.5`).
- Un valore non valido viene rifiutato, mai arrotondato.
- È unico per il gioco, non per la singola partita.
- Un gioco in backlog non può avere un voto.
- I giochi senza voto non contano nelle medie: un voto mancante non equivale a zero.

### Date

Le date si inseriscono nel formato `GG/MM/AAAA` e vengono salvate in formato ISO (`AAAA-MM-GG`).

| Campo | Regola |
|---|---|
| Data di inizio | facoltativa; se lasciata vuota diventa oggi |
| Data di completamento | solo per le partite `completed`; se lasciata vuota diventa oggi |
| Entrambe | mai nel futuro; il completamento non può precedere l'inizio |

### Cambi di stato

| Cambio | Effetto |
|---|---|
| → `playing` / `dropped` | la data di inizio diventa oggi, se mancante |
| → `completed` | inizio e completamento diventano oggi, se mancanti; con 0 ore vengono richieste le ore |
| `completed` → `playing` / `dropped` | la data di completamento viene rimossa, dopo conferma |

### Duplicati

Due giochi sono considerati duplicati se hanno **lo stesso titolo**, senza distinzione tra maiuscole e minuscole. Aggiungendo un titolo già presente, l'applicazione propone di aggiungere una nuova partita al gioco esistente.

### File danneggiato

Se il file della libreria non è leggibile, o è in un formato non riconosciuto, viene rinominato in `game_library_corrupted.json` per consentire il recupero dei dati, e l'applicazione parte con una libreria vuota.

## CSV

L'esportazione crea il file `questlog_export.csv` nella cartella del progetto; l'importazione legge lo stesso file.

### Formato

Una riga per partita: titolo e voto si ripetono su ogni partita dello stesso gioco. Un gioco in backlog occupa una riga con le sole colonne di titolo e voto (vuoto).

```
title;rating;platform;status;hours_played;start_date;completion_date
Hades;9.0;PC;completed;40.0;2026-01-01;2026-02-01
Hades;9.0;Switch;playing;5.0;2026-11-06;
Celeste;;;;;;
```

- Separatore **punto e virgola** e codifica **UTF-8**, per aprire il file direttamente nell'Excel italiano.
- Una cella vuota indica un valore mancante.
- In importazione sono accettati anche i decimali con la virgola (`2,5`) e le date `GG/MM/AAAA`.

### Importazione

- L'importazione **sostituisce** l'intera libreria, dopo conferma.
- Le righe con lo stesso titolo diventano un unico gioco con più partite.
- Ogni riga è validata con le stesse regole della libreria. Al primo errore l'importazione si ferma indicando la riga, e la libreria resta invariata.
- Modificando il file in Excel, va salvato come **CSV UTF-8**.

### Limiti noti

Il CSV esportato usa il punto per i decimali: l'Excel italiano può mostrare le ore come testo anziché come numero.

## Roadmap

- [x] **CLI**: gestione completa della libreria con persistenza JSON
- [x] **Python intermedio**: classi, type hints, test automatici con pytest, voto e date, più partite per gioco, importazione ed esportazione CSV
- [ ] **Analisi dei dati**: statistiche con pandas e grafici con matplotlib
- [ ] **Applicazione desktop**: interfaccia grafica e integrazione con il catalogo IGDB
- [ ] **Pubblicazione**: eseguibile scaricabile

## Licenza

Distribuito con licenza MIT. Vedi il file [LICENSE](LICENSE).
