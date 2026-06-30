# Smart Study Rooms

Smart Study Rooms e un progetto universitario IoT per monitorare in tempo reale due aule studio e suggerire quale sia la piu adatta allo studio in base a temperatura, umidita, rumore e presenza.

## Obiettivo

Il sistema raccoglie dati ambientali da due nodi IoT indipendenti, li invia a Firebase Realtime Database e li mostra in un'app Android nativa scritta in Java. L'app calcola uno score da 0 a 100 per ogni aula e indica automaticamente l'aula consigliata.

## Architettura

Flusso generale:

```text
Sensori -> Microcontrollore -> Wi-Fi -> Firebase Realtime Database -> App Android
```

Ogni aula ha un nodo IoT separato:

- Nodo Aula 1: Arduino UNO R4 WiFi, DHT11/DHT22, sensore rumore analogico KY-037/KY-038, PIR opzionale.
- Nodo Aula 2: Arduino UNO R4 WiFi o ESP32 con gli stessi sensori.

Il firmware aggiorna solo il proprio nodo Firebase:

- `rooms/room1`
- `rooms/room2`

Lo score viene calcolato lato Android, cosi il microcontrollore resta semplice e si occupa solo di leggere e inviare dati.

## Struttura del progetto

```text
.
├── android/                         # App Android Java/XML
│   ├── build.gradle
│   ├── settings.gradle
│   └── app/
│       ├── build.gradle
│       ├── google-services.json.example
│       └── src/main/
│           ├── AndroidManifest.xml
│           ├── java/com/example/smartstudyrooms/
│           │   ├── MainActivity.java
│           │   ├── Room.java
│           │   └── RoomScoreCalculator.java
│           └── res/
│               ├── drawable/
│               ├── layout/activity_main.xml
│               └── values/
├── arduino/
│   └── SmartStudyRoomNode/SmartStudyRoomNode.ino
├── firebase/
│   ├── database.rules.json
│   └── sample-data.json
└── simulator/
    └── firebase_simulator.py
```

## Firebase Realtime Database

La struttura consigliata del database e:

```json
{
  "rooms": {
    "room1": {
      "name": "Aula 1",
      "temperature": 22.4,
      "humidity": 48,
      "noise": 35,
      "presence": true,
      "lastUpdate": 1710000000000
    },
    "room2": {
      "name": "Aula 2",
      "temperature": 24.1,
      "humidity": 52,
      "noise": 61,
      "presence": false,
      "lastUpdate": 1710000000000
    }
  }
}
```

Nota: `lastUpdate` e gestito come timestamp Unix in millisecondi. Il firmware Arduino usa il server timestamp di Firebase con `{ ".sv": "timestamp" }`, quindi non serve sincronizzare un orologio sul microcontrollore.

### Regole temporanee

Durante il prototipo puoi usare le regole in [firebase/database.rules.json](firebase/database.rules.json):

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

Queste regole sono solo per test. Non sono sicure per produzione perche permettono lettura e scrittura pubblica a chiunque conosca l'URL del database.

## Configurare Firebase

1. Vai su [Firebase Console](https://console.firebase.google.com/).
2. Crea un nuovo progetto.
3. Aggiungi un'app Android con package name:
   `com.example.smartstudyrooms`
4. Scarica il file `google-services.json`.
5. Copialo in:
   `android/app/google-services.json`
6. Crea un Realtime Database.
7. Imposta temporaneamente le regole di test presenti in `firebase/database.rules.json`.
8. Prendi nota dell'host del database, ad esempio:
   `smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app`

## App Android

L'app Android usa:

- Java
- XML layout
- Firebase Realtime Database SDK
- Due card, una per aula
- Aggiornamento realtime tramite `ValueEventListener`
- Calcolo dello score lato app
- Barre visuali per temperatura, umidita e rumore
- Notifiche locali quando il rumore di un'aula supera `70/100`
- Preferenze di studio che modificano i pesi dello score
- Gestione dati mancanti ed errori di connessione

Classi principali:

- `MainActivity.java`: legge `rooms` da Firebase, aggiorna la UI e confronta le aule.
- `Room.java`: modello dati compatibile con Firebase.
- `RoomScoreCalculator.java`: calcola score, stato testuale e descrizione del rumore.

Su Android 13 o superiore l'app chiede il permesso notifiche al primo avvio. Le notifiche rumore vengono inviate quando un'aula supera `70/100`; l'avviso viene riattivato solo dopo che il rumore scende almeno sotto `60/100`, per evitare notifiche ripetute.

La tendina "Preferenza di studio" permette di cambiare il criterio di valutazione:

- `Bilanciata`: pesi standard.
- `Priorita silenzio`: il rumore pesa di piu nello score.
- `Priorita comfort`: temperatura e umidita diventano piu importanti.
- `Priorita aula libera`: la presenza pesa di piu per preferire aule probabilmente meno occupate.

Per aprire l'app:

1. Apri la cartella `android/` con Android Studio.
2. Inserisci `google-services.json` in `android/app/`.
3. Sincronizza Gradle.
4. Esegui l'app su emulatore o dispositivo fisico.

## Logica dello score

Lo score massimo e 100:

- Temperatura: max 35 punti
- Rumore: max 35 punti
- Umidita: max 20 punti
- Presenza: max 10 punti

Classificazione:

- `score >= 80`: Consigliata
- `score >= 60`: Accettabile
- `score >= 40`: Poco adatta
- `score < 40`: Sconsigliata

La presenza ha un peso leggero: un'aula senza presenza rilevata riceve un piccolo bonus perche potrebbe essere piu libera.

## Firmware Arduino

Il firmware si trova in:

[arduino/SmartStudyRoomNode/SmartStudyRoomNode.ino](arduino/SmartStudyRoomNode/SmartStudyRoomNode.ino)

Funzioni principali:

- Connessione Wi-Fi
- Lettura DHT11/DHT22
- Lettura sensore rumore analogico
- Lettura PIR opzionale
- Creazione JSON
- Invio HTTP `PUT` a Firebase Realtime Database
- Invio periodico ogni 10 secondi
- Modalita simulazione integrata

Per duplicare il nodo:

```cpp
const char* ROOM_ID = "room1";
const char* ROOM_NAME = "Aula 1";
```

Per il secondo nodo basta cambiare:

```cpp
const char* ROOM_ID = "room2";
const char* ROOM_NAME = "Aula 2";
```

### Librerie Arduino

Installa dall'Arduino IDE Library Manager:

- `WiFiS3`
- `ArduinoHttpClient`
- `DHT sensor library` di Adafruit
- `Adafruit Unified Sensor`

Poi configura nel file `.ino`:

- `WIFI_SSID`
- `WIFI_PASSWORD`
- `FIREBASE_HOST`
- `ROOM_ID`
- `ROOM_NAME`
- `DHT_TYPE`
- pin dei sensori

### Come testare il codice Arduino

1. Installa Arduino IDE da [arduino.cc](https://www.arduino.cc/en/software).

2. Installa il supporto per Arduino UNO R4 WiFi:

   ```text
   Tools > Board > Boards Manager
   ```

   Cerca e installa:

   ```text
   Arduino UNO R4 Boards
   ```

   Poi seleziona:

   ```text
   Tools > Board > Arduino UNO R4 WiFi
   ```

3. Installa le librerie da:

   ```text
   Tools > Manage Libraries
   ```

   Librerie da installare:

   ```text
   WiFiS3
   ArduinoHttpClient
   DHT sensor library
   Adafruit Unified Sensor
   ```

   `WiFiS3` di solito e gia inclusa con il pacchetto della scheda, ma va verificato.

4. Apri lo sketch:

   ```text
   arduino/SmartStudyRoomNode/SmartStudyRoomNode.ino
   ```

5. Configura Wi-Fi e Firebase modificando queste costanti:

   ```cpp
   const char* ROOM_ID = "room1";
   const char* ROOM_NAME = "Aula 1";

   const char* WIFI_SSID = "YOUR_WIFI_SSID";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

   const char* FIREBASE_HOST = "YOUR_PROJECT-default-rtdb.europe-west1.firebasedatabase.app";
   ```

   Esempio:

   ```cpp
   const char* ROOM_ID = "room1";
   const char* ROOM_NAME = "Aula 1";

   const char* WIFI_SSID = "CasaMia";
   const char* WIFI_PASSWORD = "passwordwifi123";

   const char* FIREBASE_HOST = "smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app";
   ```

   `FIREBASE_HOST` deve essere scritto senza `https://` e senza `/` finale.

   Corretto:

   ```cpp
   const char* FIREBASE_HOST = "smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app";
   ```

   Sbagliato:

   ```cpp
   const char* FIREBASE_HOST = "https://smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app/";
   ```

6. Per il primo test senza sensori lascia attiva la simulazione:

   ```cpp
   #define USE_SIMULATION 1
   ```

   In questo modo Arduino genera dati finti realistici e li invia a Firebase. Quando collegherai i sensori veri, imposta:

   ```cpp
   #define USE_SIMULATION 0
   ```

7. Collega Arduino UNO R4 WiFi al PC con USB.

8. Seleziona la porta:

   ```text
   Tools > Port
   ```

9. Premi il pulsante Upload, cioe la freccia verso destra.

10. Apri il Serial Monitor:

    ```text
    Tools > Serial Monitor
    ```

    Imposta la velocita a:

    ```text
    115200 baud
    ```

    Se tutto funziona dovresti vedere messaggi simili:

    ```text
    Connecting to Wi-Fi: ...
    Connected. IP address: ...
    PUT /rooms/room1.json
    Firebase status: 200
    ```

    Uno status `200` indica che Firebase ha ricevuto correttamente i dati.

11. Controlla Firebase Console > Realtime Database. Dovresti vedere:

    ```text
    rooms
      room1
        name: "Aula 1"
        temperature: ...
        humidity: ...
        noise: ...
        presence: ...
        lastUpdate: ...
    ```

12. Per il secondo nodo usa lo stesso sketch cambiando solo:

    ```cpp
    const char* ROOM_ID = "room2";
    const char* ROOM_NAME = "Aula 2";
    ```

    Poi carica il codice sul secondo microcontrollore.

## Simulazione senza hardware

Hai due opzioni.

### 1. Simulazione nel firmware Arduino

Nel file `.ino` lascia:

```cpp
#define USE_SIMULATION 1
```

Il nodo generera dati realistici:

- temperatura tra 19 e 27 gradi
- umidita tra 35 e 70%
- rumore tra 20 e 80
- presenza casuale

Quando avrai i sensori, imposta:

```cpp
#define USE_SIMULATION 0
```

### 2. Simulatore Python

Lo script [simulator/firebase_simulator.py](simulator/firebase_simulator.py) invia dati finti per `room1` e `room2` direttamente a Firebase usando l'API REST.

Esempio:

```bash
python simulator/firebase_simulator.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Per fermarlo usa `CTRL+C`.

## Possibili sviluppi futuri

- Aggiunta di piu aule.
- Storico dei dati ambientali.
- Grafici temporali nell'app.
- Notifiche quando un'aula diventa rumorosa.
- Autenticazione utenti Firebase.
- Prenotazione aula.
- Dashboard web per amministratori.
- Sensori CO2 o qualita dell'aria.
- Machine learning per prevedere occupazione o comfort.

## Note architetturali

Per un prototipo universitario, Firebase Realtime Database e una scelta semplice e veloce per aggiornamenti realtime. Se il progetto crescesse, una buona evoluzione sarebbe separare i dati correnti dallo storico:

```text
rooms/room1              # stato corrente
rooms/room2              # stato corrente
history/room1/<pushId>   # misure storiche
history/room2/<pushId>   # misure storiche
```

In questo modo l'app resta veloce per la schermata principale, ma puoi aggiungere grafici e analisi senza appesantire il nodo `rooms`.

## Bridge software su PC

Il progetto include un bridge locale in Python:

[bridge/bridge_server.py](bridge/bridge_server.py)

Il bridge riceve i dati dagli Arduino tramite HTTP, li valida, aggiunge un timestamp affidabile e li inoltra a Firebase. In questo modo Arduino non deve piu scrivere direttamente sul cloud.

Architettura con bridge:

```text
Arduino -> Bridge Python sul PC -> Firebase -> Android
```

Il bridge scrive:

```text
rooms/<room_id>                 # stato corrente dell'aula
history/<room_id>/<timestamp>   # copia storica della misura
```

### Perche introdurre il bridge

Il bridge rende l'architettura piu simile a un sistema IoT reale:

- Arduino invia dati a un gateway locale invece di parlare direttamente con Firebase.
- Le credenziali Firebase possono restare sul PC/gateway.
- I dati vengono validati prima di essere salvati.
- Il bridge puo salvare serie temporali storiche.
- In futuro lo stesso bridge puo ospitare notifiche avanzate, predizioni AI o logiche di controllo remoto.

### Avvio del bridge

Da terminale, nella root del progetto:

```bash
python3 bridge/bridge_server.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Su Windows, se usi il launcher Python:

```powershell
py bridge\bridge_server.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
```

Il bridge parte sulla porta `3000`:

```text
http://0.0.0.0:3000
```

Per controllare che sia attivo:

```text
http://IP_DEL_PC:3000/health
```

### Configurare Arduino per usare il bridge

Nel firmware Arduino lascia:

```cpp
#define USE_BRIDGE 1
```

Poi imposta l'indirizzo IP del PC su cui gira il bridge:

```cpp
const char* BRIDGE_HOST = "192.168.1.50";
const int BRIDGE_PORT = 3000;
```

L'IP del PC si trova con:

```powershell
ipconfig
```

Arduino e PC devono essere nella stessa rete locale. In una versione reale, lo stesso bridge potrebbe essere eseguito su Raspberry Pi come gateway locale sempre acceso, oppure spostato su cloud per rimuovere il vincolo della stessa LAN.

### Validazione dei dati

Il bridge accetta solo payload con valori coerenti:

- `temperature`: da `-10` a `50`
- `humidity`: da `0` a `100`
- `noise`: da `0` a `100`
- `presence`: `true` oppure `false`

Se un dato e fuori range, il bridge risponde con errore `400` e non aggiorna Firebase.

### Test manuale del bridge

Puoi inviare una misura finta senza Arduino:

```bash
curl -X POST http://localhost:3000/rooms/room1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Aula 1","temperature":22.4,"humidity":48,"noise":35,"presence":true}'
```

Se tutto funziona, Firebase viene aggiornato in:

```text
rooms/room1
history/room1/<timestamp>
```

Per disattivare il salvataggio storico:

```bash
python3 bridge/bridge_server.py --database-host smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app --no-history
```
