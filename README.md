# Questlog

Applicazione da terminale per catalogare la propria libreria di videogiochi e tenere traccia di stato e ore di gioco.

> Progetto in sviluppo. Questa è la versione a riga di comando: le prossime fasi aggiungeranno statistiche, grafici e un'interfaccia desktop.

## Funzionalità

- **Aggiunta** di un gioco con titolo, piattaforma, stato e ore giocate.
- **Visualizzazione** della libreria numerata.
- **Ricerca** per titolo, parziale e senza distinzione tra maiuscole e minuscole.
- **Filtro** per stato.
- **Modifica** di titolo, piattaforma, stato e ore.
- **Eliminazione** con richiesta di conferma.
- **Salvataggio automatico** dopo ogni modifica e caricamento all'avvio.
- **Validazione** di ogni dato inserito: campi vuoti, numeri non validi, duplicati.

## Requisiti e avvio

- Python 3.10 o superiore
- Nessuna libreria esterna

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

### Modifiche

- Un gioco con ore registrate non può tornare in `backlog`.
- Passando a `completed`, le ore vengono richieste se sono 0, altrimenti è possibile aggiornarle.
- Inserendo le ore di un gioco in `backlog`, il gioco passa a `playing` dopo conferma.

### Duplicati

Due giochi sono considerati duplicati se hanno **stesso titolo e stessa piattaforma**, senza distinzione tra maiuscole e minuscole. Lo stesso gioco può quindi essere presente su piattaforme diverse.

### File danneggiato

Se il file della libreria non è leggibile, viene rinominato in `game_library_corrupted.json` per consentire il recupero dei dati, e l'applicazione parte con una libreria vuota.

## Roadmap

- [x] **CLI**: gestione completa della libreria con persistenza JSON
- [ ] **Python intermedio**: classi, type hints, test automatici con pytest, importazione ed esportazione CSV, voto personale e date
- [ ] **Analisi dei dati**: statistiche con pandas e grafici con matplotlib
- [ ] **Applicazione desktop**: interfaccia grafica e integrazione con il catalogo IGDB
- [ ] **Pubblicazione**: eseguibile scaricabile

## Licenza

Distribuito con licenza MIT. Vedi il file [LICENSE](LICENSE).