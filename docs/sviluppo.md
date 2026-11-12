# Questlog · documentazione tecnica

Come installare, configurare e sviluppare Questlog, e le regole della libreria nel dettaglio. Per una presentazione dell'app vedi il [README](../README.md).

## Requisiti e avvio

- Python 3.12 o superiore
- Le librerie di `requirements.txt`: PySide6 per l'interfaccia, supabase per account e database, requests e python-dotenv per IGDB, pandas e matplotlib per le statistiche, pytest e mypy per lo sviluppo

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

La versione a riga di comando si avvia con `python cli.py`.

La cartella `data/` è esclusa dal repository e contiene i dati di questo computer: la sessione dell'account (`session.json`), la cache delle copertine e delle traduzioni, gli export, e la libreria locale delle versioni precedenti.

### Account e database (Supabase)

Senza configurazione l'app funziona in **modalità locale**: niente login, libreria nel file `data/game_library.json`. Per usare gli account:

1. Crea un progetto su [supabase.com](https://supabase.com). Nelle impostazioni dell'API lascia attiva la *Data API* e attiva l'RLS automatica.
2. Nel **SQL Editor** esegui `supabase/schema.sql`: crea le tabelle, le regole RLS e la funzione `replace_library`.
   I file in `supabase/updates/` servono solo a chi aveva già creato il database con una versione precedente dello schema.
3. In **Authentication → Sign In / Providers**:
   - **Email**: attivo, con *Confirm email* acceso e lunghezza minima della password 8;
   - **Google**: Client ID e Client Secret di un client OAuth *Web application* creato su Google Cloud, con redirect `https://<progetto>.supabase.co/auth/v1/callback`.
4. In **Authentication → URL Configuration** aggiungi ai *Redirect URLs* `http://localhost:8765/callback`.
5. Nel `.env` inserisci `SUPABASE_URL` (l'URL del progetto, senza `/rest/v1`) e `SUPABASE_ANON_KEY` (la chiave *publishable/anon*).

Il login con Google e la conferma dell'email riportano il browser su `http://localhost:8765/callback`: per qualche minuto l'app ascolta su quella porta, solo sul tuo computer, e riceve il codice da scambiare con la sessione (flusso OAuth **PKCE**).

### Catalogo IGDB

Il catalogo viene da [IGDB](https://www.igdb.com). Servono le credenziali di un'app registrata su [dev.twitch.tv](https://dev.twitch.tv/console):

1. Copia `.env.example` come `.env`.
2. Inserisci `IGDB_CLIENT_ID` e `IGDB_CLIENT_SECRET`.

Il file `.env` è escluso dal repository. Senza credenziali l'app usa un piccolo catalogo di prova.

Le descrizioni di IGDB sono in inglese. Per vederle in italiano si può aggiungere nel `.env` una chiave dell'[API DeepL](https://www.deepl.com/pro-api) (`DEEPL_API_KEY`). Ogni descrizione viene tradotta una volta sola e salvata in cache.

### Sicurezza: quali chiavi vanno dove

| Chiave | Dove | Perché |
|---|---|---|
| `SUPABASE_ANON_KEY` (publishable) | `.env` e app | è pubblica per progetto: da sola non legge nessun dato, ci pensano login e RLS |
| chiave *secret* / `service_role` di Supabase | **mai** nell'app né su GitHub | salta le regole RLS: chi l'ha legge e cancella i dati di tutti |
| Client Secret di Google | solo nelle impostazioni di Supabase | il login con Google passa da Supabase, l'app non lo usa |
| `IGDB_CLIENT_SECRET` | `.env`, per ora | da spostare in una Edge Function prima di distribuire l'app (Fase 7) |
| `data/session.json` | solo sul tuo computer | contiene i token dell'account: equivale a una password |

Tabelle e funzione sono accessibili solo agli utenti con il login fatto (`authenticated`), e le regole **RLS** fanno vedere a ognuno solo le proprie righe. `replace_library` gira con i permessi di chi la chiama (`security invoker`) e in un'unica transazione: o la libreria viene salvata tutta, o non cambia niente.

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
  storage.py        libreria su file JSON (modalità locale)
  cloud.py          Supabase: client, sessione, login con email e con Google
  cloud_repository.py  libreria nel database Supabase e controlli prima dell'invio
  catalog.py        catalogo dei giochi: interfaccia e versione di prova
  igdb.py           catalogo IGDB
  platforms.py      nomi uniformi delle piattaforme
  csv_io.py         import ed export CSV
  wrapped.py        statistiche in stile Wrapped
  analysis.py       statistiche con pandas
  charts.py         grafici matplotlib (versione terminale)
  translation.py    traduzione delle descrizioni
ui/               app desktop PySide6: pagine, widget, stile (style.qss), icone e font
supabase/         schema del database (tabelle, RLS, funzioni) e aggiornamenti
terminal/         versione a riga di comando
tests/            test con pytest
```

L'interfaccia non contiene regole: le chiede a `core`. Le pagine comunicano con segnali e la finestra principale (`ui/main_window.py`) decide la navigazione. Le richieste a IGDB e a Supabase girano in background per non bloccare la finestra.

Con l'account, le pagine usano `ui/cloud_library.py`: una copia della libreria in memoria, letta da Supabase al login. Ogni modifica si vede subito e parte verso il database in background, un invio alla volta e sempre con la versione più recente; alla chiusura e al logout le ultime modifiche vengono inviate prima di uscire.

## Account

- Con Supabase configurato, l'accesso è **obbligatorio**: senza login si vede solo la pagina Accedi / Registrati.
- Ogni account ha la sua libreria; un account nuovo parte vuoto, con l'invito ad aggiungere il primo gioco.
- La sessione resta salvata: al riavvio si entra senza rifare il login. **Esci** salva le ultime modifiche e svuota la libreria dalla finestra.
- Registrandosi con email arriva un link di conferma: cliccandolo su questo computer si entra direttamente. Aperto altrove, conferma comunque l'account e poi si accede con la password.
- **Libreria del PC**: se l'account è vuoto e c'è `data/game_library.json`, l'app propone di caricarlo. I giochi che il database rifiuterebbe (per esempio un voto fuori scala) vengono elencati e restano solo nel file. Dopo il caricamento il file viene rinominato in `game_library_uploaded.json` e la proposta non compare più.

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
