# Smart Study Rooms

Smart Study Rooms è un progetto universitario IoT per monitorare in tempo reale due aule studio e suggerire quale aula sia più adatta allo studio in base a temperatura, umidità e rumore.

Il progetto include:

- due nodi Arduino UNO senza Wi-Fi, collegati al PC via USB seriale;
- un bridge Python eseguito sul PC;
- Firebase Realtime Database;
- un'app Android nativa in Java/XML;
- calcolo score e preferenze utente;
- notifiche locali quando un'aula diventa troppo rumorosa;
- storico dati su Firebase tramite bridge.

## Architettura del progetto

L'architettura reale del progetto è la seguente:

```text
Nodo Aula 1
Arduino UNO n.1 + sensori
        |
        | USB seriale
        v
serial_to_bridge.py sul PC
        |
        | HTTP locale
        v
Bridge Python sul PC
        |
        | REST API Firebase
        v
Firebase Realtime Database
        |
        | SDK Firebase Android
        v
App Android
```

```text
Nodo Aula 2
Arduino UNO n.2 + sensori
        |
        | USB seriale
        v
serial_to_bridge.py sul PC
        |
        | HTTP locale
        v
Bridge Python sul PC
        |
        | REST API Firebase
        v
Firebase Realtime Database
        |
        | SDK Firebase Android
        v
App Android
```

In modo compatto:

```text
Arduino UNO n.1 -> USB seriale -> serial_to_bridge.py -> Bridge Python -> Firebase -> Android
Arduino UNO n.2 -> USB seriale -> serial_to_bridge.py -> Bridge Python -> Firebase -> Android
```

Il bridge rappresenta il punto centrale del sistema. Riceve dati da sorgenti diverse, li valida, aggiunge un timestamp affidabile e aggiorna Firebase.

## Perchè esiste il bridge

Il bridge software simula un gateway IoT locale.

Serve a:

- evitare che ogni microcontrollore debba parlare direttamente con Firebase;
- validare i dati prima di salvarli;
- aggiungere `lastUpdate` lato PC/gateway;
- salvare sia lo stato corrente sia lo storico;
- unificare nodi diversi, cioè i due Arduino UNO via seriale;
- preparare il progetto a sviluppi futuri come AI, notifiche cloud o controllo remoto.

In una versione reale, il bridge potrebbe girare su Raspberry Pi, server locale o cloud. In questo prototipo gira su PC.

## Struttura cartelle

```text
.
├── android/                                # App Android Java/XML
│   ├── app/
│   │   ├── google-services.json.example
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── java/com/example/smartstudyrooms/
│   │       │   ├── MainActivity.java
│   │       │   ├── Room.java
│   │       │   └── RoomScoreCalculator.java
│   │       └── res/
│   ├── build.gradle
│   ├── gradle.properties
│   └── settings.gradle
├── arduino/
│   ├── SmartStudyRoomNode/                        # Vecchio sketch Arduino Wi-Fi/direct/bridge
    └── SmartStudyRoomSerialNode/
        ├── SmartStudyRoomSerialNode1              # Sketch Arduino UNO n.1 senza Wi-Fi
│       └── SmartStudyRoomSerialNode2              # Sketch Arduino UNO n.2 senza Wi-Fi
├── bridge/
│   ├── bridge_server.py              # Bridge HTTP -> Firebase
│   ├── serial_to_bridge.py           # Lettura seriale Arduino UNO -> bridge
│   └── requirements.txt              # Dipendenza pyserial
├── firebase/
│   ├── database.rules.json
│   └── sample-data.json
└── simulator/
    └── firebase_simulator.py
```

## Componenti hardware

### Aula 1

Nodo consigliato:

- Arduino UNO n.1 senza modulo Wi-Fi;
- sensore temperatura/umidità DHT22;
- sensore rumore analogico KY-037;
- collegamento USB al PC.

Sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode1.ino
```

### Aula 2

Nodo disponibile:

- Arduino UNO n.2 senza modulo Wi-Fi;
- sensore temperatura/umidità DHT22;
- sensore rumore analogico KY-037;
- collegamento USB al PC.

Sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode2.ino
```

## Struttura Firebase

Il bridge aggiorna lo stato corrente delle aule in:

```text
rooms/room1
rooms/room2
```

Esempio:

```json
{
  "rooms": {
    "room1": {
      "name": "Aula 1",
      "temperature": 22.4,
      "humidity": 48,
      "noise": 35,
      "lastUpdate": 1710000000000,
      "source": "bridge"
    },
    "room2": {
      "name": "Aula 2",
      "temperature": 24.1,
      "humidity": 52,
      "noise": 61,
      "lastUpdate": 1710000000000,
      "source": "bridge"
    }
  }
}
```

Il bridge salva anche uno storico:

```text
history/room1/<timestamp>
history/room2/<timestamp>
```

Esempio:

```json
{
  "history": {
    "room1": {
      "1710000000000": {
        "name": "Aula 1",
        "temperature": 22.4,
        "humidity": 48,
        "noise": 35,
        "lastUpdate": 1710000000000,
        "source": "bridge"
      }
    }
  }
}
```

## Regole Firebase per prototipo

Per test iniziale puoi usare:

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

Le trovi in:

```text
firebase/database.rules.json
```

Attenzione: queste regole sono solo per test. Non sono sicure in produzione perchè chiunque conosca l'URL del database potrebbe leggere o scrivere dati.

## Configurare Firebase

1. Vai su Firebase Console.
2. Crea un progetto.
3. Crea un Realtime Database.
4. Imposta temporaneamente le regole di test.
5. Aggiungi un'app Android con package name:

```text
com.example.smartstudyrooms
```

6. Scarica `google-services.json`.
7. Copialo in:

```text
android/app/google-services.json
```

8. Prendi nota dell'host del database, ad esempio:

```text
smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Questo host serve per avviare il bridge.

## Installazione software sul PC

Servono:

- Python 3;
- Arduino IDE;
- Android Studio;
- eventuale driver USB per Arduino;
- librerie Arduino per DHT.

### Installare dipendenze Python

Da terminale nella root del progetto:

```powershell
py -m pip install -r bridge\requirements.txt
```

Su Linux/macOS:

```bash
python3 -m pip install -r bridge/requirements.txt
```

`requirements.txt` installa `pyserial`, usato per leggere la seriale dell'Arduino UNO.

## Avvio completo del sistema

L'ordine consigliato e:

1. Avvia Firebase Realtime Database.
2. Avvia il bridge Python sul PC.
3. Collega Arduino UNO n.1 via USB e anche Arduino UNO n.2 via USB su un altro PC.
4. Avvia lo script `serial_to_bridge.py` per Arduino UNO.
6. Apri l'app Android.
7. Controlla Firebase.

## 1. Avviare il bridge Python

Da terminale nella root del progetto:

```powershell
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app
```

Esempio:

```powershell
py bridge\bridge_server.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Su Linux/macOS:

```bash
python3 bridge/bridge_server.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Se parte correttamente vedrai qualcosa del tipo:

```text
Smart Study Rooms bridge started
Listening on http://0.0.0.0:3000
Firebase: https://smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
History enabled: True
Press CTRL+C to stop
```

Il bridge resta in ascolto su:

```text
http://localhost:3000
```

oppure, dalla rete locale:

```text
http://IP_DEL_PC:3000
```

### Test health del bridge

Apri nel browser:

```text
http://localhost:3000/health
```

Dovresti vedere:

```json
{"status":"ok","service":"smart-study-rooms-bridge"}
```

Se Arduino non riesce a contattare il bridge, controlla anche Windows Firewall. Se compare una richiesta di autorizzazione per Python, consenti l'accesso sulla rete privata.

## 2. Test manuale del bridge senza hardware

Puoi inviare dati finti al bridge con curl:

```powershell
curl -X POST http://localhost:3000/rooms/room1 `
  -H "Content-Type: application/json" `
  -d '{"name":"Aula 1","temperature":22.4,"humidity":48,"noise":35}'
```

Su Linux/macOS:

```bash
curl -X POST http://localhost:3000/rooms/room1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Aula 1","temperature":22.4,"humidity":48,"noise":35}'
```

Se funziona, Firebase mostrera:

```text
rooms/room1
history/room1/<timestamp>
```

## 3. Configurare Arduino UNO senza Wi-Fi (vale per entrambi)

Apri lo sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode1.ino 
```
oppure

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode2.ino 
```

Per il primo test lascia:

```cpp
#define USE_SIMULATION 1
```

Così Arduino genera dati finti senza sensori.

Quando userai i sensori reali:

```cpp
#define USE_SIMULATION 0
```

Configura il nome aula se necessario (vale per entrambe le aule):

```cpp
const char* ROOM_NAME = "Aula 1";
```
oppure

```cpp
const char* ROOM_NAME = "Aula 2";
```

Carica lo sketch su Arduino UNO.

Apri il Serial Monitor a:

```text
115200 baud
```

Dovresti vedere una riga JSON ogni 10 secondi:

```json
{"name":"Aula 1","temperature":22.4,"humidity":48.0,"noise":35}
```

Questa riga non va direttamente a Firebase. Viene letta dallo script `serial_to_bridge.py`.

## 4. Avviare serial_to_bridge.py

Lascia il bridge acceso nel primo terminale.

In un secondo terminale avvia:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room1 --bridge-url http://localhost:3000
```

`COM3` è solo un esempio. La porta corretta la trovi in Arduino IDE:

```text
Tools > Port
```

Esempi comuni:

```text
COM3
COM4
COM5
```

Su Linux/macOS potrebbe essere:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room1 --bridge-url http://localhost:3000
```

Se funziona vedrai:

```text
Arduino serial forwarder started
Serial <- {"name":"Aula 1",...}
Bridge -> HTTP 200: {...}
```

Firebase verra aggiornato in:

```text
rooms/room1
history/room1/<timestamp>
```

## 5. Avviare l'app Android

Apri Android Studio e seleziona la cartella Android del progetto.

Se lavori su Windows, conviene usare una copia locale tipo:

```text
C:\Users\leonardo.levrini\Documents\SmartStudyRoomsAndroid
```

Non e consigliato aprire direttamente:

```text
\\wsl.localhost\Ubuntu\...
```

perchè Android Studio e Gradle possono essere lenti o instabili su percorsi WSL/UNC.

Controlla che esista:

```text
android/app/google-services.json
```

Poi fai:

```text
Sync Gradle
Run app
```

L'app legge da Firebase:

```text
rooms/room1
rooms/room2
```

e mostra:

- nome aula;
- temperatura;
- umidita;
- rumore;
- ultimo aggiornamento;
- score;
- stato;
- aula consigliata;
- barre visuali;
- preferenza di studio;
- notifiche rumore alto.

## Score dell'aula

Lo score viene calcolato lato Android, non su Arduino.

Componenti principali:

- temperatura;
- rumore;
- umidità.

Classificazione:

```text
score >= 80       -> Consigliata
score >= 60       -> Accettabile
score >= 40       -> Poco adatta
score < 40        -> Sconsigliata
```

L'utente può cambiare preferenza di studio:

- `Bilanciata`;
- `Priorita silenzio`;
- `Priorita comfort`.

La preferenza modifica i pesi dello score.

## Notifiche Android

L'app può inviare notifiche locali quando il rumore supera la soglia:

```text
noise >= 70
```

L'avviso viene riattivato solo quando il rumore scende sotto:

```text
noise <= 60
```

Questo evita notifiche ripetute continue.

Su Android 13 o superiore l'app chiede il permesso notifiche al primo avvio.

## Validazione dati nel bridge

Il bridge accetta solo dati coerenti:

```text
temperature: -10 .. 50
humidity: 0 .. 100
noise: 0 .. 100
```

Se un dato è fuori range, il bridge risponde con errore `400` e non aggiorna Firebase.

Esempio dato rifiutato:

```json
{"temperature":999,"humidity":48,"noise":35}
```

## Troubleshooting

### Il bridge non parte

Controlla che Python sia installato:

```powershell
py --version
```

Controlla che il comando contenga il database host senza `https://`:

Corretto:

```text
smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Sbagliato:

```text
https://smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app/
```

### Arduino UNO non invia dati

Controlla:

- Serial Monitor impostato a `115200 baud`;
- porta corretta in `serial_to_bridge.py`;
- Arduino IDE non deve tenere occupata la porta mentre lo script Python la usa;
- se il Serial Monitor è aperto, chiudilo prima di avviare `serial_to_bridge.py`.

### Firebase non si aggiorna

Controlla:

- regole Firebase temporanee `.read` e `.write` a `true`;
- database host corretto;
- bridge acceso;
- risposta HTTP del bridge;
- console Firebase su `rooms/room1` e `rooms/room2`.

### Android Studio non vede l'emulatore

Apri:

```text
Tools > Device Manager
```

Crea un virtual device, ad esempio Pixel 6 o Pixel 5.

Se il progetto è lento o Gradle da problemi, aprilo da una cartella Windows locale invece che da WSL.

## Modalita di test consigliata

Per testare tutto senza sensori reali:

1. Imposta `USE_SIMULATION 1` su Arduino UNO n.1.
2. Imposta `USE_SIMULATION 1` su Arduino UNO n.2.
3. Avvia il bridge.
4. Avvia `serial_to_bridge.py`.
5. Controlla Firebase.
6. Apri app Android.

Se funziona, vedrai:

```text
rooms/room1 aggiornato dall'Arduino UNO n.1 via seriale
rooms/room2 aggiornato dall'Arduino UNO n.2 via seriale
history/room1 popolato
history/room2 popolato
app Android aggiornata in realtime
```

## Possibili sviluppi futuri

- Bridge su Raspberry Pi come gateway locale sempre acceso.
- Bridge cloud per eliminare il vincolo della stessa rete Wi-Fi.
- Autenticazione Firebase piu sicura.
- Notifiche push tramite Firebase Cloud Messaging.
- Dashboard web.
- Storico dati con grafici temporali.
- Predizioni AI based su rumore, score o occupazione.
- Attuatori fisici: LED RGB, display OLED, buzzer.
- Sensori CO2 o qualita dell'aria.
- Supporto dinamico a piu aule.
- Prenotazione aula.

## Frase riassuntiva per presentazione

```text
Smart Study Rooms crea un digital twin di ogni aula studio: i nodi IoT raccolgono dati ambientali, il bridge software li valida e li sincronizza su Firebase, mentre l'app Android mostra lo stato realtime delle aule e suggerisce quella più adatta allo studio.
```

## Predizioni ML based

La cartella `lm/` contiene una prima pipeline di machine learning:

```text
lm/predictor.py
lm/requirements.txt
```

Lo script legge lo storico da Firebase:

```text
history/<room_id>/<timestamp>
```

e lo trasforma in un dataset tabellare con colonne come:

```text
temperature, humidity, noise, hour, day_of_week, score_now, target_score
```

Il target rappresenta lo score futuro dopo un certo numero di minuti. Di default:

```text
target_score = score tra 15 minuti
```

Poi lo script allena un modello:

```text
RandomForestRegressor
```

e scrive le predizioni in Firebase:

```text
predictions/room1
predictions/room2
```

Esempio di predizione salvata:

```json
{
  "currentScore": 84,
  "predictedScore": 76,
  "horizonMinutes": 15,
  "trend": "peggioramento",
  "model": "RandomForestRegressor",
  "mae": 6.2,
  "generatedAt": 1710000000000
}
```

### Installazione dipendenze ML

Da terminale nella root del progetto:

```powershell
py -m pip install -r lm\requirements.txt
```

Su Linux/macOS:

```bash
python3 -m pip install -r lm/requirements.txt
```

### Avvio predizione una tantum

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app
```

### Esportare il dataset in CSV

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app --export-csv dataset.csv
```

Questo comando crea un file `dataset.csv` con le righe usate dal modello. E' utile per controllare cosa sta imparando il modello e per mostrarlo nella relazione.

### Esecuzione continua

Aggiorna le predizioni ogni 60 secondi:

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app --loop --interval 60
```

Per funzionare bene, servono abbastanza dati in `history/`. Con pochi minuti di storico il modello potrebbe non avere righe sufficienti per allenarsi, perche deve trovare coppie:

```text
situazione attuale -> score futuro
```

Per esempio, con `--horizon-minutes 15`, lo script deve trovare misure distanti almeno 15 minuti tra loro.
