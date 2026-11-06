# Questlog

Applicazione da terminale per catalogare la propria libreria di videogiochi e tenere traccia di stato, ore di gioco, voti e date.

> Progetto in sviluppo. Questa è la versione a riga di comando: le prossime fasi aggiungeranno statistiche, grafici e un'interfaccia desktop.

## Funzionalità

- **Aggiunta** di un gioco con titolo, piattaforma, stato, ore giocate, voto e date.
- **Visualizzazione** della libreria numerata.
- **Scheda** con tutti i dettagli di un gioco.
- **Ricerca** per titolo, parziale e senza distinzione tra maiuscole e minuscole.
- **Filtro** per stato.
- **Modifica** di titolo, piattaforma, stato, ore, voto e date.
- **Eliminazione** con richiesta di conferma.
- **Date automatiche** nei cambi di stato.
- **Salvataggio automatico** dopo ogni modifica e caricamento all'avvio.
- **Validazione** di ogni dato inserito: campi vuoti, numeri e date non validi, duplicati.

## Requisiti e avvio

- Python 3.10 o superiore
- Nessuna libreria esterna per usare l'applicazione

```bash
python main.py
```

La libreria viene salvata nel file `game_library.json`, nella cartella del progetto. Il file è escluso dal repository perché contiene dati personali.

### Sviluppo

Per eseguire i test serve un ambiente virtuale con le dipendenze di sviluppo:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

## Regole della libreria

### Stati

| Stato | Significato |
|---|---|
| `backlog` | posseduto, mai iniziato |
| `playing` | in corso |
| `completed` | completato |
| `dropped` | abbandonato |

### Ore giocate

| Situazione | Regola |
|---|---|
| Gioco in `backlog` | ore sempre a 0, non vengono richieste |
| Gioco `playing` o `dropped` | ore richieste, 0 ammesso |
| Gioco `completed` | ore richieste, maggiori di 0 |
| Qualsiasi gioco | ore mai negative, valori non numerici rifiutati |

### Voto

- Facoltativo, da 1 a 10, con mezzi punti ammessi (es. `7.5`).
- Un valore non valido viene rifiutato, mai arrotondato.
- Un gioco in `backlog` non può avere un voto.
- I giochi senza voto non contano nelle medie: un voto mancante non equivale a zero.

### Date

Le date si inseriscono nel formato `GG/MM/AAAA` e vengono salvate in formato ISO (`AAAA-MM-GG`).

| Campo | Regola |
|---|---|
| Data di inizio | facoltativa; mai per i giochi in `backlog` |
| Data di completamento | facoltativa; solo per i giochi `completed` |
| Entrambe | mai nel futuro; il completamento non può precedere l'inizio |

### Cambi di stato

| Cambio | Effetto |
|---|---|
| `backlog` → `playing` / `dropped` | la data di inizio diventa oggi, se mancante |
| → `completed` | inizio e completamento diventano oggi, se mancanti |
| `completed` → `playing` / `dropped` | la data di completamento viene rimossa, dopo conferma |
| → `backlog` | solo con 0 ore; voto e data di inizio vengono rimossi, dopo conferma |

Inserendo le ore di un gioco in `backlog`, il gioco passa a `playing` dopo conferma.

### Duplicati

Due giochi sono considerati duplicati se hanno **stesso titolo e stessa piattaforma**, senza distinzione tra maiuscole e minuscole. Lo stesso gioco può quindi essere presente su piattaforme diverse.

### File danneggiato

Se il file della libreria non è leggibile, viene rinominato in `game_library_corrupted.json` per consentire il recupero dei dati, e l'applicazione parte con una libreria vuota.

## Roadmap

- [x] **CLI**: gestione completa della libreria con persistenza JSON
- [ ] **Python intermedio**: classi, type hints e test automatici con pytest ✅, voto e date ✅, importazione ed esportazione CSV
- [ ] **Analisi dei dati**: statistiche con pandas e grafici con matplotlib
- [ ] **Applicazione desktop**: interfaccia grafica e integrazione con il catalogo IGDB
- [ ] **Pubblicazione**: eseguibile scaricabile

## Licenza

Distribuito con licenza MIT. Vedi il file [LICENSE](LICENSE).