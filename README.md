# Questlog

Applicazione desktop per catalogare la propria libreria di videogiochi: cerchi i giochi nel catalogo di IGDB, li aggiungi alla libreria, registri le partite e scopri come giochi con statistiche in stile "Wrapped".

Scritta in Python con PySide6 (Qt). Include anche una versione a riga di comando che usa la stessa logica.

## Funzionalità

- **Home**: il gioco che stai giocando in primo piano, con lo sfondo del gioco, i numeri della libreria e i giochi giocati di recente.
- **Libreria**: griglia di copertine che si adatta alla finestra, ricerca per titolo e filtro per stato.
- **Catalogo IGDB**: ricerca tra tutti i giochi esistenti, con le sezioni *Di tendenza*, *Nuove uscite* e *In arrivo*.
- **Scheda del gioco**: copertina, sfondo, descrizione, piattaforme e screenshot da IGDB; voto da 1 a 5 stelle; partite con piattaforma, stato, ore, date e note, da aggiungere, modificare ed eliminare.
- **Statistiche in stile Wrapped**: ore totali, gioco più giocato, top 5, console preferita, partite completate, voto medio, durata media e profilo da giocatore, per sempre o anno per anno.
- **Importa ed esporta** la libreria in CSV, con anteprima e conferma prima di sostituire i dati.
- **Collega a IGDB** i giochi inseriti a mano, per dare loro copertina e descrizione.
- **Tutto in una finestra**: conferme, form ed errori compaiono nella pagina, senza finestre di dialogo.

## Requisiti e avvio

- Python 3.10 o superiore
- Le librerie di `requirements.txt`: PySide6 per l'interfaccia, requests e python-dotenv per IGDB, pandas e matplotlib per le statistiche, pytest e mypy per lo sviluppo

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

La versione a riga di comando si avvia con `python cli.py`.

I dati personali sono nella cartella `data/`, esclusa dal repository: la libreria (`game_library.json`), la cache delle copertine e delle traduzioni, gli export.

### Catalogo IGDB

Il catalogo viene da [IGDB](https://www.igdb.com). Servono le credenziali di un'app registrata su [dev.twitch.tv](https://dev.twitch.tv/console):

1. Copia `.env.example` come `.env`.
2. Inserisci `IGDB_CLIENT_ID` e `IGDB_CLIENT_SECRET`.

Il file `.env` è escluso dal repository. Senza credenziali l'app usa un piccolo catalogo di prova.

Le descrizioni di IGDB sono in inglese. Per vederle in italiano si può aggiungere nel `.env` una chiave dell'[API DeepL](https://www.deepl.com/pro-api) (`DEEPL_API_KEY`). Ogni descrizione viene tradotta una volta sola e salvata in cache.

### Sviluppo

```bash
pytest
python -m mypy cli.py app.py tests
```

## Struttura del progetto

```
app.py            avvio dell'app desktop
cli.py            avvio della versione a riga di comando
core/             logica pura, senza interfaccia, condivisa e testata
  models.py         Game e Playthrough
  library.py        regole della libreria
  repository.py     salvataggio della libreria (pattern Repository)
  catalog.py        catalogo dei giochi: interfaccia e versione di prova
  igdb.py           catalogo IGDB
  platforms.py      nomi uniformi delle piattaforme
  csv_io.py         import ed export CSV
  wrapped.py        statistiche in stile Wrapped
  analysis.py       statistiche con pandas
  charts.py         grafici matplotlib (versione terminale)
  translation.py    traduzione delle descrizioni
ui/               app desktop PySide6: pagine, widget e stile (style.qss)
terminal/         versione a riga di comando
tests/            test con pytest
```

L'interfaccia non contiene regole: le chiede a `core`. Le pagine comunicano con segnali e la finestra principale (`ui/main_window.py`) decide la navigazione. Le richieste a IGDB girano in background per non bloccare la finestra.

## Regole della libreria

### Giochi e partite

Un gioco ha un titolo, un voto e zero o più partite. Piattaforma, stato, ore e date appartengono alla singola partita, mentre il voto è unico per il gioco.

- Un gioco **senza partite** è in **backlog**: posseduto, mai iniziato.
- Eliminando l'ultima partita, il gioco torna in backlog e perde il voto, dopo conferma.
- Le ore totali del gioco sono la somma delle ore di tutte le partite.
- Lo stesso gioco può avere più partite, anche sulla stessa piattaforma.
- Le piattaforme hanno un **nome unico**: `ps4`, `PS4` e `PlayStation 4` diventano tutte `PlayStation 4`, in ogni punto da cui entrano (app, terminale, IGDB, CSV). Le piattaforme non riconosciute restano come sono state scritte.

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

- Facoltativo, da 1 a 5 stelle (solo numeri interi).
- Un valore non valido viene rifiutato, mai arrotondato.
- È unico per il gioco, non per la singola partita.
- Un gioco in backlog non può avere un voto.
- I giochi senza voto non contano nelle medie: un voto mancante non equivale a zero.

### Date

Le date si mostrano nel formato `GG/MM/AAAA` (nell'app con un calendario) e vengono salvate in formato ISO (`AAAA-MM-GG`).

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

Due giochi sono considerati duplicati se hanno **lo stesso titolo**, senza distinzione tra maiuscole e minuscole, oppure lo stesso **id IGDB**. Aprendo dal catalogo un gioco già in libreria con lo stesso titolo, viene collegato a IGDB invece di essere duplicato.

### File danneggiato

Se il file della libreria non è leggibile, o è in un formato non riconosciuto, viene rinominato in `game_library_corrupted.json` per consentire il recupero dei dati, e l'applicazione parte con una libreria vuota.

## CSV

Dall'app: avatar in alto a destra → **Importa ed esporta**. Il file si sceglie con la finestra di sistema.

### Formato

Una riga per partita: titolo, voto e dati IGDB si ripetono su ogni partita dello stesso gioco. Un gioco in backlog occupa una riga senza dati di partita.

```
title;rating;platform;status;hours_played;start_date;completion_date;notes;igdb_id;cover_url
Hades;5;PC;completed;40.0;2026-01-01;2026-02-01;tutti i finali;1;https://...
Celeste;;;;;;;;;
```

- Separatore **punto e virgola** e codifica **UTF-8**, per aprire il file direttamente nell'Excel italiano.
- Una cella vuota indica un valore mancante.
- `notes`, `igdb_id` e `cover_url` sono facoltative in importazione, così si importano anche i CSV delle versioni precedenti.
- Sono accettati anche i decimali con la virgola (`2,5`) e le date `GG/MM/AAAA`.

### Importazione

- L'importazione **sostituisce** l'intera libreria, dopo un'anteprima e una conferma.
- Le righe con lo stesso titolo diventano un unico gioco con più partite.
- Ogni riga è validata con le stesse regole della libreria. Al primo errore l'importazione si ferma indicando la riga, e la libreria resta invariata.
- Modificando il file in Excel, va salvato come **CSV UTF-8**.

## Statistiche

La pagina **Statistiche** racconta le abitudini di gioco con riquadri colorati, per sempre o per un singolo anno.

- Una partita appartiene all'anno in cui è stata **completata**, oppure a quello in cui è iniziata se non è finita.
- Le durate usano la **mediana** e non la media, perché un singolo gioco con moltissime ore sposterebbe la media lontano dal gioco tipico.
- Il **tasso di completamento** conta le partite completate sul totale di quelle concluse (completate + abbandonate): le partite in corso non contano.
- Il **profilo da giocatore** segue regole semplici: più di metà delle ore su un gioco → *Il Fedelissimo*; almeno l'80% delle partite concluse completate → *Il Completista*; almeno 8 giochi → *L'Esploratore*; altrimenti *Lo Stratega*.

La versione a riga di comando mostra le stesse statistiche in testo e salva quattro grafici PNG in `data/`.

## Roadmap

- [x] **CLI**: gestione completa della libreria con persistenza JSON
- [x] **Python intermedio**: classi, type hints, test con pytest, più partite per gioco, CSV
- [x] **Analisi dei dati**: statistiche con pandas e grafici con matplotlib
- [x] **Applicazione desktop**: PySide6, catalogo IGDB, scheda gioco, statistiche Wrapped
- [ ] **Cloud**: Supabase con accesso tramite Google e libreria sincronizzata
- [ ] **IGDB sicuro**: credenziali spostate in una Edge Function
- [ ] **Pubblicazione**: eseguibile `.exe` scaricabile

## Licenza

Distribuito con licenza MIT. Vedi il file [LICENSE](LICENSE).
