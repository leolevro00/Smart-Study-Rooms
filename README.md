# Smart Study Rooms

Smart Study Rooms e un progetto universitario IoT per monitorare in tempo reale due aule studio e suggerire quale aula sia piu adatta allo studio in base a temperatura, umidita, rumore e presenza.

Il progetto include:

- un nodo ESP32 con Wi-Fi;
- un nodo Arduino UNO senza Wi-Fi, collegato al PC via USB seriale;
- un bridge Python eseguito sul PC;
- Firebase Realtime Database;
- un'app Android nativa in Java/XML;
- calcolo score e preferenze utente;
- notifiche locali quando un'aula diventa troppo rumorosa;
- storico dati su Firebase tramite bridge.

## Architettura del progetto

L'architettura reale del progetto e questa:

```text
Nodo Aula 1
ESP32 + sensori
        |
        | HTTP Wi-Fi
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
Arduino UNO + sensori
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
ESP32 -> Wi-Fi HTTP -> Bridge Python -> Firebase -> Android
Arduino UNO -> USB seriale -> serial_to_bridge.py -> Bridge Python -> Firebase -> Android
```

Il bridge e il punto centrale del sistema. Riceve dati da sorgenti diverse, li valida, aggiunge un timestamp affidabile e aggiorna Firebase.

## Perche esiste il bridge

Il bridge software simula un gateway IoT locale.

Serve a:

- evitare che ogni microcontrollore debba parlare direttamente con Firebase;
- validare i dati prima di salvarli;
- aggiungere `lastUpdate` lato PC/gateway;
- salvare sia lo stato corrente sia lo storico;
- unificare nodi diversi, cioe ESP32 via Wi-Fi e Arduino UNO via seriale;
- preparare il progetto a sviluppi futuri come AI, notifiche cloud o controllo remoto.

In una versione reale, il bridge potrebbe girare su Raspberry Pi, server locale o cloud. In questo prototipo gira su PC.

## Struttura cartelle

```text
.
+-- android/                         # App Android Java/XML
|   +-- app/
|   |   +-- google-services.json.example
|   |   +-- src/main/
|   |       +-- AndroidManifest.xml
|   |       +-- java/com/example/smartstudyrooms/
|   |       |   +-- MainActivity.java
|   |       |   +-- Room.java
|   |       |   +-- RoomScoreCalculator.java
|   |       |   +-- RoomPrediction.java
|   |       +-- res/
|   +-- build.gradle
|   +-- gradle.properties
|   +-- settings.gradle
+-- arduino/
|   +-- SmartStudyRoomNode/           # Vecchio sketch Arduino Wi-Fi/direct/bridge
|   +-- SmartStudyRoomSerialNode/     # Sketch Arduino UNO senza Wi-Fi
+-- bridge/
|   +-- bridge_server.py              # Bridge HTTP -> Firebase
|   +-- serial_to_bridge.py           # Lettura seriale Arduino UNO -> bridge
|   +-- requirements.txt              # Dipendenza pyserial
+-- esp32/
|   +-- SmartStudyRoomEsp32Node/      # Sketch ESP32 Wi-Fi -> bridge
+-- firebase/
|   +-- database.rules.json
|   +-- sample-data.json
+-- lm/                               # Training e predizioni ML
|   +-- predictor.py
|   +-- requirements.txt
+-- simulator/
    +-- firebase_simulator.py
```

## Componenti hardware

### Aula 1

Nodo consigliato:

- ESP32 con Wi-Fi;
- sensore temperatura/umidita DHT11 o DHT22;
- sensore rumore analogico KY-037/KY-038 o simile;
- sensore PIR opzionale.

Sketch:

```text
esp32/SmartStudyRoomEsp32Node/SmartStudyRoomEsp32Node.ino
```

### Aula 2

Nodo disponibile:

- Arduino UNO senza modulo Wi-Fi;
- sensore temperatura/umidita DHT11 o DHT22;
- sensore rumore analogico KY-037/KY-038 o simile;
- sensore PIR opzionale;
- collegamento USB al PC.

Sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode.ino
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
      "presence": true,
      "lastUpdate": 1710000000000,
      "source": "bridge"
    },
    "room2": {
      "name": "Aula 2",
      "temperature": 24.1,
      "humidity": 52,
      "noise": 61,
      "presence": false,
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
        "presence": true,
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

Attenzione: queste regole sono solo per test. Non sono sicure in produzione, perche chiunque conosca l'URL del database potrebbe leggere o scrivere dati.

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
- eventuale driver USB per Arduino/ESP32;
- librerie Arduino per DHT e, per ESP32, supporto scheda ESP32.

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
3. Collega Arduino UNO via USB.
4. Avvia lo script `serial_to_bridge.py` per Arduino UNO.
5. Accendi o carica lo sketch ESP32.
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

Se Arduino o ESP32 non riescono a contattare il bridge, controlla anche Windows Firewall. Se compare una richiesta di autorizzazione per Python, consenti l'accesso sulla rete privata.

## 2. Test manuale del bridge senza hardware

Puoi inviare dati finti al bridge con curl:

```powershell
curl -X POST http://localhost:3000/rooms/room1 `
  -H "Content-Type: application/json" `
  -d '{"name":"Aula 1","temperature":22.4,"humidity":48,"noise":35,"presence":true}'
```

Su Linux/macOS:

```bash
curl -X POST http://localhost:3000/rooms/room1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Aula 1","temperature":22.4,"humidity":48,"noise":35,"presence":true}'
```

Se funziona, Firebase mostrera:

```text
rooms/room1
history/room1/<timestamp>
```

## 3. Configurare ESP32

Apri Arduino IDE e installa il supporto ESP32:

```text
Tools > Board > Boards Manager
```

Cerca:

```text
esp32
```

Installa il pacchetto ESP32 by Espressif Systems.

Apri lo sketch:

```text
esp32/SmartStudyRoomEsp32Node/SmartStudyRoomEsp32Node.ino
```

Configura:

```cpp
const char* ROOM_ID = "room1";
const char* ROOM_NAME = "Aula 1";

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char* BRIDGE_HOST = "192.168.1.50";
const int BRIDGE_PORT = 3000;
```

`BRIDGE_HOST` deve essere l'IP del PC su cui gira il bridge.

Su Windows lo trovi con:

```powershell
ipconfig
```

Cerca l'indirizzo IPv4 della scheda Wi-Fi, ad esempio:

```text
192.168.1.50
```

Per il primo test lascia:

```cpp
#define USE_SIMULATION 1
```

Cosi l'ESP32 genera dati finti senza sensori.

Quando userai i sensori reali:

```cpp
#define USE_SIMULATION 0
```

Carica lo sketch sull'ESP32 e apri il Serial Monitor a:

```text
115200 baud
```

Se funziona vedrai messaggi simili:

```text
Connected. IP address: ...
POST bridge http://192.168.1.50:3000/rooms/room1
Bridge status: 200
```

## 4. Configurare Arduino UNO senza Wi-Fi

Apri lo sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode.ino
```

Per il primo test lascia:

```cpp
#define USE_SIMULATION 1
```

Cosi Arduino genera dati finti senza sensori.

Quando userai i sensori reali:

```cpp
#define USE_SIMULATION 0
```

Configura il nome aula se necessario:

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
{"name":"Aula 2","temperature":22.4,"humidity":48.0,"noise":35,"presence":true}
```

Questa riga non va direttamente a Firebase. Viene letta dallo script `serial_to_bridge.py`.

## 5. Avviare serial_to_bridge.py

Lascia il bridge acceso nel primo terminale.

In un secondo terminale avvia:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room2 --bridge-url http://localhost:3000
```

`COM3` e solo un esempio. La porta corretta la trovi in Arduino IDE:

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
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room2 --bridge-url http://localhost:3000
```

Se funziona vedrai:

```text
Arduino serial forwarder started
Serial <- {"name":"Aula 2",...}
Bridge -> HTTP 200: {...}
```

Firebase verra aggiornato in:

```text
rooms/room2
history/room2/<timestamp>
```

## 6. Avviare l'app Android

Apri Android Studio e seleziona la cartella Android del progetto.

Se lavori su Windows, conviene usare una copia locale tipo:

```text
C:\Users\leonardo.levrini\Documents\SmartStudyRoomsAndroid
```

Non e consigliato aprire direttamente:

```text
\\wsl.localhost\Ubuntu\...
```

perche Android Studio e Gradle possono essere lenti o instabili su percorsi WSL/UNC.

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
- presenza;
- ultimo aggiornamento;
- score;
- stato;
- aula consigliata;
- barre visuali;
- preferenza di studio;
- notifiche rumore alto.

## Score dell'aula

Lo score e calcolato lato Android, non su Arduino.

Componenti principali:

- temperatura;
- rumore;
- umidita;
- presenza.

Classificazione:

```text
score >= 80       -> Consigliata
score >= 60       -> Accettabile
score >= 40       -> Poco adatta
score < 40        -> Sconsigliata
```

L'utente puo cambiare preferenza di studio:

- `Bilanciata`;
- `Priorita silenzio`;
- `Priorita comfort`;
- `Priorita aula libera`.

La preferenza modifica i pesi dello score.

## Notifiche Android

L'app puo inviare notifiche locali quando il rumore supera la soglia:

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
presence: true/false
```

Se un dato e fuori range, il bridge risponde con errore `400` e non aggiorna Firebase.

Esempio dato rifiutato:

```json
{"temperature":999,"humidity":48,"noise":35,"presence":true}
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

### ESP32 non raggiunge il bridge

Controlla:

- ESP32 e PC devono essere sulla stessa rete Wi-Fi;
- `BRIDGE_HOST` deve essere l'IP IPv4 del PC;
- il bridge deve essere acceso;
- Windows Firewall deve permettere a Python di ricevere connessioni;
- prova dal browser `http://IP_DEL_PC:3000/health`.

### Arduino UNO non invia dati

Controlla:

- Serial Monitor impostato a `115200 baud`;
- porta corretta in `serial_to_bridge.py`;
- Arduino IDE non deve tenere occupata la porta mentre lo script Python la usa;
- se il Serial Monitor e aperto, chiudilo prima di avviare `serial_to_bridge.py`.

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

Se il progetto e lento o Gradle da problemi, aprilo da una cartella Windows locale invece che da WSL.

## Modalita di test consigliata

Per testare tutto senza sensori reali:

1. Imposta `USE_SIMULATION 1` su ESP32.
2. Imposta `USE_SIMULATION 1` su Arduino UNO.
3. Avvia il bridge.
4. Avvia `serial_to_bridge.py`.
5. Accendi ESP32.
6. Controlla Firebase.
7. Apri app Android.

Se funziona, vedrai:

```text
rooms/room1 aggiornato dall'ESP32
rooms/room2 aggiornato dall'Arduino UNO via seriale
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
Smart Study Rooms crea un digital twin di ogni aula studio: i nodi IoT raccolgono dati ambientali, il bridge software li valida e li sincronizza su Firebase, mentre l'app Android mostra lo stato realtime delle aule e suggerisce quella piu adatta allo studio.
```

## Predizioni ML based

La cartella `lm/` contiene la parte di machine learning del progetto:

```text
lm/predictor.py
lm/requirements.txt
```

Lo script `predictor.py` usa lo storico salvato dal bridge in Firebase:

```text
history/room1/<timestamp>
history/room2/<timestamp>
```

Da quello storico crea un dataset tabellare con colonne come:

```text
room_id, timestamp, temperature, humidity, noise, presence, hour, day_of_week, score_now, target_score
```

Il campo piu importante e `target_score`: rappresenta lo score futuro dell'aula dopo un certo numero di minuti.

Esempio:

```text
situazione attuale alle 10:00 -> score futuro alle 10:15
```

Di default lo script predice lo score tra 15 minuti:

```text
--horizon-minutes 15
```

Per test veloci, soprattutto se hai pochi dati nello storico, puoi usare:

```text
--horizon-minutes 1
```

Il modello usato e:

```text
RandomForestRegressor
```

Quando gli passi anche `--database-host`, lo script salva il risultato su Firebase in:

```text
predictions/room1
predictions/room2
```

Esempio di predizione salvata:

```json
{
  "currentScore": 67,
  "predictedScore": 73,
  "horizonMinutes": 1,
  "trend": "miglioramento",
  "model": "RandomForestRegressor",
  "mae": 11.65,
  "generatedAt": 1785938286274
}
```

L'app Android legge questi nodi e mostra la predizione dentro le card delle aule.

## Prima cosa: scegliere come usare il predictor

Ci sono due modi corretti per usare `lm/predictor.py`.

### Modo A: leggere direttamente lo storico da Firebase

Usi questo modo quando il database contiene gia il nodo:

```text
history
```

In questo caso lo script scarica da solo lo storico da Firebase, allena il modello e salva le predizioni.

Schema:

```text
Firebase history -> predictor.py -> Firebase predictions -> app Android
```

Questo e il modo piu comodo quando il bridge e gia stato usato per un po' e ha popolato lo storico.

### Modo B: usare un JSON esportato manualmente da Firebase

Usi questo modo quando hai scaricato un file `.json` dalla console Firebase.

Schema:

```text
file JSON locale -> predictor.py -> terminale oppure Firebase predictions -> app Android
```

Questo e utile se vuoi fare prove offline, controllare il dataset o lavorare su uno storico esportato.

Se usi un JSON locale e vuoi anche vedere la predizione nell'app Android, devi comunque aggiungere `--database-host`, perche senza quello lo script stampa solo il risultato nel terminale.

## Installazione dipendenze ML su Windows PowerShell

Apri PowerShell nella root del progetto.

Se il progetto Android e stato copiato in Windows ma il repository principale e su WSL, puoi usare una cartella Windows oppure aprire PowerShell nella cartella del repo se e accessibile.

Installa le dipendenze:

```powershell
py -m pip install -r lm\requirements.txt
```

Se `py` non funziona, prova:

```powershell
python -m pip install -r lm\requirements.txt
```

Le librerie installate sono:

```text
pandas
numpy
scikit-learn
```

## Modo A da Windows: leggere direttamente Firebase

Questo comando legge `history` da Firebase, allena il modello e salva le predizioni in `predictions`.

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app
```

Esempio realistico:

```powershell
py lm\predictor.py --database-host smartstudyrooms-659ff-default-rtdb.europe-west1.firebasedatabase.app
```

Importante: devi scrivere solo l'host, senza `https://` e senza slash finale.

Corretto:

```text
smartstudyrooms-659ff-default-rtdb.europe-west1.firebasedatabase.app
```

Sbagliato:

```text
https://smartstudyrooms-659ff-default-rtdb.europe-west1.firebasedatabase.app/
```

Per esportare anche il dataset CSV usato dal modello:

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app --export-csv dataset.csv
```

Per fare una predizione a 1 minuto invece che a 15 minuti:

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app --horizon-minutes 1
```

Per aggiornare le predizioni in modo continuo ogni 60 secondi:

```powershell
py lm\predictor.py --database-host TUO_DATABASE.firebasedatabase.app --loop --interval 60
```

Con questo comando puoi lasciare il predictor acceso durante la demo.

## Modo B da Windows: usare un JSON esportato da Firebase

Se hai scaricato da Firebase lo storico di una sola aula, per esempio `history/room2`, devi specificare anche `--room-id room2`.

Esempio:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\room2-export.json" --room-id room2 --export-csv dataset-room2.csv --horizon-minutes 1
```

Questo comando:

- legge il JSON locale;
- crea `dataset-room2.csv`;
- allena il modello;
- stampa la predizione nel terminale;
- non salva nulla su Firebase.

Se vuoi salvare la predizione anche su Firebase, aggiungi `--database-host`:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\room2-export.json" --room-id room2 --export-csv dataset-room2.csv --horizon-minutes 1 --database-host TUO_DATABASE.firebasedatabase.app
```

Per `room1` e uguale, cambi solo file e room id:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\room1-export.json" --room-id room1 --export-csv dataset-room1.csv --horizon-minutes 1 --database-host TUO_DATABASE.firebasedatabase.app
```

Se invece hai esportato tutto il database oppure tutto il nodo `history`, `--room-id` non e necessario perche dentro il JSON sono gia presenti `room1` e `room2`.

Esempio:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\history-export.json" --export-csv dataset.csv --horizon-minutes 1 --database-host TUO_DATABASE.firebasedatabase.app
```

## Installazione dipendenze ML su WSL

Su Ubuntu/WSL recente potresti vedere questo errore se provi a usare `pip` globalmente:

```text
This environment is externally managed
```

E normale. Significa che Ubuntu non vuole che tu installi pacchetti Python globali con `pip`. La soluzione corretta e usare un virtual environment dentro il progetto.

Entra nella cartella del progetto:

```bash
cd /home/leolevro/uni/Smart-Study-Rooms
```

Crea il virtual environment:

```bash
python3 -m venv .venv
```

Se il comando fallisce, installa il supporto a `venv`:

```bash
sudo apt update
sudo apt install python3-venv
```

Poi ripeti:

```bash
python3 -m venv .venv
```

Attiva l'ambiente:

```bash
source .venv/bin/activate
```

Quando e attivo vedrai il prefisso `(.venv)` nel terminale.

Installa le dipendenze ML:

```bash
pip install -r lm/requirements.txt
```

Da questo momento, finche l'ambiente e attivo, usa `python` invece di `python3`:

```bash
python lm/predictor.py --help
```

Ogni volta che riapri WSL e vuoi usare il modello ML, devi solo fare:

```bash
cd /home/leolevro/uni/Smart-Study-Rooms
source .venv/bin/activate
```

Quando hai finito puoi uscire dall'ambiente virtuale con:

```bash
deactivate
```

## Modo A da WSL: leggere direttamente Firebase

Con l'ambiente virtuale attivo:

```bash
python lm/predictor.py --database-host TUO_DATABASE.firebasedatabase.app
```

Esempio:

```bash
python lm/predictor.py --database-host smartstudyrooms-659ff-default-rtdb.europe-west1.firebasedatabase.app
```

Per esportare anche il dataset:

```bash
python lm/predictor.py \
  --database-host TUO_DATABASE.firebasedatabase.app \
  --export-csv dataset.csv
```

Per predire a 1 minuto:

```bash
python lm/predictor.py \
  --database-host TUO_DATABASE.firebasedatabase.app \
  --horizon-minutes 1
```

Per aggiornare continuamente Firebase ogni 60 secondi:

```bash
python lm/predictor.py \
  --database-host TUO_DATABASE.firebasedatabase.app \
  --loop \
  --interval 60
```

## Modo B da WSL: usare un JSON esportato da Firebase

Da WSL i percorsi Windows cambiano forma.

Un file Windows come:

```text
C:\Users\leonardo.levrini\Downloads\room2-export.json
```

da WSL diventa:

```text
/mnt/c/Users/leonardo.levrini/Downloads/room2-export.json
```

Quindi, se hai esportato solo `history/room2`, usa:

```bash
python lm/predictor.py \
  --history-json "/mnt/c/Users/leonardo.levrini/Downloads/room2-export.json" \
  --room-id room2 \
  --export-csv dataset-room2.csv \
  --horizon-minutes 1
```

Questo comando lavora solo localmente: crea il CSV e stampa la predizione nel terminale.

Per salvare anche la predizione su Firebase e farla vedere nell'app Android:

```bash
python lm/predictor.py \
  --history-json "/mnt/c/Users/leonardo.levrini/Downloads/room2-export.json" \
  --room-id room2 \
  --export-csv dataset-room2.csv \
  --horizon-minutes 1 \
  --database-host TUO_DATABASE.firebasedatabase.app
```

Per `room1`:

```bash
python lm/predictor.py \
  --history-json "/mnt/c/Users/leonardo.levrini/Downloads/room1-export.json" \
  --room-id room1 \
  --export-csv dataset-room1.csv \
  --horizon-minutes 1 \
  --database-host TUO_DATABASE.firebasedatabase.app
```

Se il file JSON si trova in un percorso lungo, per esempio dentro WhatsApp Desktop, puoi copiarlo prima dentro il progetto:

```bash
cp "/mnt/c/Users/leonardo.levrini/AppData/Local/Packages/5319275A.WhatsAppDesktop_cv1g1gvanyjgm/LocalState/sessions/BDE12E98136BD255E3B4C51836C01D37A39E2FBA/transfers/2026-31/smartstudyrooms-659ff-default-rtdb-room2-export.json" ./room2-history.json
```

Poi il comando diventa piu leggibile:

```bash
python lm/predictor.py \
  --history-json room2-history.json \
  --room-id room2 \
  --export-csv dataset-room2.csv \
  --horizon-minutes 1 \
  --database-host TUO_DATABASE.firebasedatabase.app
```

## Come capire se il predictor ha funzionato

Se funziona, nel terminale vedrai qualcosa di simile:

```json
{
  "predictions": {
    "room2": {
      "currentScore": 67,
      "predictedScore": 73,
      "horizonMinutes": 1,
      "trend": "miglioramento",
      "model": "RandomForestRegressor",
      "mae": 11.65,
      "generatedAt": 1785938286274
    }
  }
}
```

Vedrai anche:

```text
Training rows: 590
MAE: 11.65
```

`Training rows` indica quante righe sono state usate per allenare il modello.

`MAE` indica l'errore medio del modello. Piu e basso, meglio e. Per esempio `MAE: 11.65` significa che in media il modello sbaglia di circa 11.65 punti sullo score.

Se hai usato `--database-host`, controlla Firebase:

```text
predictions/room1
predictions/room2
```

Se compare solo `predictions/room2`, significa che nel dataset avevi solo dati di `room2`. Per avere anche `room1`, devi avere dati in `history/room1` oppure usare un JSON esportato da `history/room1`.

## Visualizzare le predizioni nell'app Android

L'app Android legge automaticamente:

```text
predictions/room1
predictions/room2
```

Quando `lm/predictor.py` salva una predizione su Firebase, ogni card mostra:

```text
Predizione ML: 73/100 tra 1 min
Trend previsto: miglioramento
Modello: RandomForestRegressor | MAE: 11.6
```

Se l'app non mostra la predizione, controlla questi punti:

- il predictor e stato lanciato con `--database-host`;
- in Firebase esiste `predictions/room1` oppure `predictions/room2`;
- il package Android usa il `google-services.json` corretto;
- le regole Firebase permettono la lettura;
- hai dati sufficienti nello storico per allenare il modello.

## Errori comuni del predictor

### Nessun dato valido trovato nello storico

Significa che il JSON o il nodo Firebase non contiene misure valide con:

```text
temperature, humidity, noise, presence
```

### Il file sembra l'export di una singola aula

Se vedi un errore simile, aggiungi `--room-id`.

Esempio:

```bash
python lm/predictor.py \
  --history-json room2-history.json \
  --room-id room2
```

### Servono almeno 10 righe con target futuro

Il modello non ha abbastanza dati per imparare.

Soluzioni:

- lascia girare il bridge piu a lungo;
- abbassa temporaneamente `--horizon-minutes`, per esempio a `1`;
- verifica che `history/room1` o `history/room2` contenga abbastanza misure.
