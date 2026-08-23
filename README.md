# Smart Study Rooms

Smart Study Rooms è un progetto universitario IoT per monitorare in tempo reale due aule studio e suggerire quale aula sia più adatta allo studio in base a temperatura, umidità e rumore.


Smart Study Rooms crea un digital twin di ogni aula studio: i nodi IoT raccolgono dati ambientali, il bridge software li valida e li sincronizza su Firebase, mentre l'app Android mostra lo stato realtime delle aule e suggerisce quella piu adatta allo studio.


Il progetto include:

- due nodi Arduino UNO senza Wi-Fi, collegati al PC via USB seriale;
- un bridge Python eseguito sul PC;
- Firebase Realtime Database;
- un'app Android nativa in Java/XML;
- calcolo score e preferenze utente;
- notifiche locali quando un'aula diventa troppo rumorosa;
- storico dati su Firebase tramite bridge;
- attuatori fisici con LED rosso/verde per temperatura e LED giallo per aula consigliata.

## Indice rapido

Usa questa legenda per saltare subito ai punti principali del progetto:

1. [Come far partire tutto il sistema](#come-far-partire-tutto-il-sistema)
2. [Configurare Firebase](#configurare-firebase)
3. [Avviare il bridge Python](#1-avviare-il-bridge-python)
4. [Test manuale senza hardware](#2-test-manuale-del-bridge-senza-hardware)
5. [Configurare Arduino UNO per Aula 1](#3-configurare-arduino-uno-per-aula-1)
6. [Configurare Arduino UNO per Aula 2](#4-configurare-arduino-uno-per-aula-2)
7. [Avviare serial_to_bridge.py per entrambe le aule](#5-avviare-serial_to_bridgepy-per-entrambe-le-aule)
8. [Due PC, un solo bridge](#due-pc-un-solo-bridge)
9. [Avviare l'app Android](#6-avviare-lapp-android)
10. [Predizioni ML based](#predizioni-ml-based)
11. [Attuatori e LED](#attuatori-e-led)
12. [Troubleshooting](#troubleshooting)

## Architettura del progetto

L'architettura reale attuale del progetto e questa:

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

Il bridge rappresenta il punto centrale del sistema. Riceve i dati dai due script seriali, li valida, aggiunge un timestamp affidabile e aggiorna Firebase. Inoltre calcola quale aula sia migliore e manda ai due Arduino il comando per accendere o spegnere il LED giallo dell'aula consigliata.

## Perchè esiste il bridge

Il bridge software simula un gateway IoT locale.

Serve a:
- evitare che ogni microcontrollore debba parlare direttamente con Firebase;
- validare i dati prima di salvarli;
- aggiungere `lastUpdate` lato PC/gateway;
- salvare sia lo stato corrente sia lo storico;
- unificare i due Arduino UNO collegati via seriale;
- preparare il progetto a sviluppi futuri come AI, notifiche cloud o controllo remoto;
- gestire gli attuatori fisici, per esempio il LED giallo acceso solo sull'aula migliore.

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
|   +-- SmartStudyRoomNode/           # Sketch legacy/non usato nella demo attuale
|   +-- SmartStudyRoomSerialNode/
|       +-- SmartStudyRoomSerialNode1.ino  # Arduino UNO Aula 1
|       +-- SmartStudyRoomSerialNode2.ino  # Arduino UNO Aula 2
+-- bridge/
|   +-- bridge_server.py              # Bridge HTTP -> Firebase
|   +-- serial_to_bridge.py           # Lettura seriale Arduino UNO -> bridge
|   +-- requirements.txt              # Dipendenza pyserial
+-- esp32/                            # Codice sperimentale non usato nella demo attuale
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

Nodo utilizzato:

- Arduino UNO n.1 senza modulo Wi-Fi;
- sensore temperatura/umidità DHT22;
- sensore rumore analogico KY-037;
- attuatori;
- collegamento USB al PC.

Sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode1.ino
```

### Aula 2

Nodo utilizzato:

- Arduino UNO n.2 senza modulo Wi-Fi;
- sensore temperatura/umidità DHT22;
- sensore rumore analogico KY-037;
- attuatori;
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
recommendation
actuators/room1
actuators/room2
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

## Attuatori e LED

Il progetto usa anche tre LED su ogni Arduino UNO:

```text
LED verde   -> simula raffrescamento/condizionatore
LED rosso   -> simula riscaldamento
LED giallo  -> indica che questa è l'aula consigliata
```

### LED rosso e verde

Questi due LED sono gestiti direttamente da Arduino in base alla temperatura letta dal sensore:

```text
temperatura > 25 °C  -> LED verde acceso, raffrescamento simulato
temperatura < 20 °C  -> LED rosso acceso, riscaldamento simulato
20 °C <= temperatura <= 25 °C -> entrambi spenti
```

Questa logica resta locale perchè dipende solo dalla temperatura della singola aula.

### LED giallo aula consigliata

Il LED giallo invece dipende dal confronto tra `room1` e `room2`, quindi non può essere deciso dal singolo Arduino da solo.

La logica è la seguente:

```text
Arduino room1 -> serial_to_bridge -> bridge
Arduino room2 -> serial_to_bridge -> bridge
bridge calcola score room1 e room2 con la stessa logica Android e con la preferenza scelta all'avvio
bridge decide bestRoomId
bridge salva recommendation e actuators su Firebase
serial_to_bridge legge /actuators/<room_id>
serial_to_bridge manda BEST_LED_ON oppure BEST_LED_OFF ad Arduino
Arduino accende o spegne il LED giallo
```

La preferenza scelta dall'app viene salvata in Firebase:

```text
settings/studyPreference = balanced | comfort | quiet
```

Il bridge legge questo valore e ricalcola l'aula migliore con gli stessi pesi usati dall'app.

Il bridge garantisce che nello stato logico solo una stanza abbia:

```json
{"bestRoomLed": true}
```

Esempio su Firebase:

```json
{
  "recommendation": {
    "bestRoomId": "room1",
    "bestRoomName": "Aula 1",
    "room1Score": 87,
    "room2Score": 61,
    "preference": "quiet",
    "preferenceLabel": "Priorita silenzio",
    "updatedAt": 1710000000000
  },
  "actuators": {
    "room1": {
      "bestRoomLed": true
    },
    "room2": {
      "bestRoomLed": false
    }
  }
}
```

Sullo sketch Arduino il LED giallo è collegato al pin:

```cpp
const int YELLOW_LED_PIN = 11;
```

I comandi seriali riconosciuti da Arduino sono:

```text
BEST_LED_ON
BEST_LED_OFF
```

Non serve modificare l'app Android per questa feature: l'app continua a leggere Firebase e mostrare score/aula consigliata. La decisione fisica dei LED viene gestita dal bridge, in modo da funzionare anche se l'app non è aperta. La preferenza del LED giallo viene letta da Firebase da `settings/studyPreference`, quindi quando cambi preferenza dall'app cambia anche la logica del bridge. Il parametro `--study-preference` resta solo come valore iniziale se l'app non ha ancora scritto nulla.
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

Per il test iniziale puoi usare:

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

Attenzione: queste regole sono solo per test. Non sono sicure in produzione, perchè chiunque conosca l'URL del database potrebbe leggere o scrivere dati.

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

## Come far partire tutto il sistema

Questa è la procedura completa consigliata per avviare l'intero ecosistema Smart Study Rooms durante un test o una demo.

### Prima di iniziare

Controlla di avere:

- Firebase Realtime Database creato;
- regole Firebase temporanee abilitate per test;
- file `google-services.json` presente in `android/app/google-services.json`;
- Python installato;
- dipendenze del bridge installate;
- Android Studio pronto con emulatore o telefono fisico;
- Arduino UNO n.1 collegato via USB;
- Arduino UNO n.2 collegato via USB;
- porta seriale del primo Arduino nota, ad esempio `COM3`;
- porta seriale del secondo Arduino nota, ad esempio `COM4`.

### Ordine di avvio consigliato

1. Apri Firebase Console e tieni d'occhio i nodi `rooms`, `history` e `predictions`.
2. Apri il primo terminale e avvia il bridge Python.
3. Verifica che il bridge risponda su `/health`.
4. Collega Arduino UNO n.1 e Arduino UNO n.2 via USB.
5. Apri il secondo terminale e avvia `serial_to_bridge.py` per `room1`.
6. Apri il terzo terminale e avvia `serial_to_bridge.py` per `room2`.
7. Controlla che Firebase riceva `rooms/room1`, `rooms/room2`, `recommendation` e `actuators`.
8. Apri Android Studio e avvia l'app.
9. Se vuoi usare anche le predizioni, avvia `lm/predictor.py` in un altro terminale.
10. Controlla che l'app mostri dati realtime, score, aula consigliata e predizioni.
11. Controlla che un solo LED giallo sia acceso: deve essere quello dell'aula con score migliore.

### Terminale 1: bridge Python

Da Windows PowerShell, nella root del progetto:

```powershell
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app
```

Puoi anche scegliere la preferenza usata dal bridge per decidere quale LED giallo accendere:

```powershell
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app --study-preference balanced
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app --study-preference comfort
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app --study-preference quiet
```

Da WSL/Linux:

```bash
python3 bridge/bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app --study-preference balanced
```

Se funziona, il bridge deve mostrare:

```text
Listening on http://0.0.0.0:3000
History enabled: True
```

Lascia questo terminale aperto.

### Test rapido del bridge

Apri nel browser:

```text
http://localhost:3000/health
```

Risultato atteso:

```json
{"status":"ok","service":"smart-study-rooms-bridge"}
```

Se questo test non funziona, non andare avanti: prima risolvi il bridge.

### Terminale 2: Arduino UNO Aula 1

Dopo aver collegato Arduino UNO n.1 via USB, trova la porta seriale da Arduino IDE:

```text
Tools > Port
```

Poi avvia il forwarder seriale per `room1`.

Esempio Windows:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room1 --bridge-url http://localhost:3000
```

Esempio Linux/WSL:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room1 --bridge-url http://localhost:3000
```

Se funziona, Firebase deve aggiornare:

```text
rooms/room1
history/room1/<timestamp>
```

Lascia questo terminale aperto.

### Terminale 3: Arduino UNO Aula 2

Dopo aver collegato Arduino UNO n.2 via USB, trova la seconda porta seriale.

Esempio Windows:

```powershell
py bridge\serial_to_bridge.py --port COM4 --room-id room2 --bridge-url http://localhost:3000
```

Esempio Linux/WSL:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM1 --room-id room2 --bridge-url http://localhost:3000
```

Se funziona, Firebase deve aggiornare:

```text
rooms/room2
history/room2/<timestamp>
```

Lascia aperto anche questo terminale.

### Android app

Apri Android Studio, sincronizza Gradle e avvia l'app su emulatore o telefono.

L'app deve leggere:

```text
rooms/room1
rooms/room2
predictions/room1
predictions/room2
```

Nella schermata principale dovresti vedere:

- dati realtime delle due aule;
- score di ogni aula;
- stato dell'aula;
- aula consigliata;
- eventuali predizioni ML;
- notifiche se il rumore supera la soglia.

### Terminale 4 opzionale: predizioni ML

Se vuoi mostrare anche la parte AI based, avvia il predictor.

Da WSL con ambiente virtuale attivo:

```bash
source .venv/bin/activate
python lm/predictor.py \
  --database-host TUO_DATABASE.firebasedatabase.app \
  --horizon-minutes 1 \
  --loop \
  --interval 60
```

Questo comando aggiorna Firebase ogni 60 secondi.

Se in Firebase esistono sia `history/room1` sia `history/room2`, lo script crea automaticamente:

```text
predictions/room1
predictions/room2
```

Se esiste solo `history/room2`, verra creata solo `predictions/room2`.

### Controllo finale su Firebase

Alla fine dell'avvio dovresti vedere almeno:

```text
rooms
  room1
  room2

history
  room1
  room2

settings
  studyPreference

recommendation
actuators
  room1
  room2
```

Se hai avviato anche il predictor:

```text
predictions
  room1
  room2
```

### Riassunto super rapido per demo

```text
1. Firebase aperto
2. Terminale 1: bridge_server.py
3. Browser: http://localhost:3000/health
4. Terminale 2: serial_to_bridge.py --room-id room1
5. Terminale 3: serial_to_bridge.py --room-id room2
6. Android Studio: Run app
7. Terminale 4 opzionale: predictor.py --loop
```

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

Se gli script Python non riescono a contattare il bridge, controlla anche Windows Firewall. Se compare una richiesta di autorizzazione per Python, consenti l'accesso sulla rete privata.

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

## 3. Configurare Arduino UNO per Aula 1

Apri lo sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode1.ino
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

Controlla che il nome aula sia:

```cpp
const char* ROOM_NAME = "Aula 1";
```

Carica lo sketch su Arduino UNO n.1.

Apri il Serial Monitor a:

```text
115200 baud
```

Dovresti vedere una riga JSON ogni 10 secondi:

```json
{"name":"Aula 1","temperature":22.4,"humidity":48.0,"noise":35,"presence":true}
```

Questa riga non va direttamente a Firebase. Viene letta dallo script `serial_to_bridge.py` con `--room-id room1`.

## 4. Configurare Arduino UNO per Aula 2

Apri lo sketch:

```text
arduino/SmartStudyRoomSerialNode/SmartStudyRoomSerialNode2.ino
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

Controlla che il nome aula sia:

```cpp
const char* ROOM_NAME = "Aula 2";
```

Carica lo sketch su Arduino UNO n.2.

Apri il Serial Monitor a:

```text
115200 baud
```

Dovresti vedere una riga JSON ogni 10 secondi:

```json
{"name":"Aula 2","temperature":22.4,"humidity":48.0,"noise":35,"presence":true}
```

Questa riga non va direttamente a Firebase. Viene letta dallo script `serial_to_bridge.py` con `--room-id room2`.

## 5. Avviare serial_to_bridge.py per entrambe le aule

Lascia il bridge acceso nel primo terminale.

Poi apri due terminali separati: uno per Aula 1 e uno per Aula 2.

### Aula 1

Esempio Windows:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room1 --bridge-url http://localhost:3000
```

Esempio Linux/WSL:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room1 --bridge-url http://localhost:3000
```

Firebase verra aggiornato in:

```text
rooms/room1
history/room1/<timestamp>
```

### Aula 2

Esempio Windows:

```powershell
py bridge\serial_to_bridge.py --port COM4 --room-id room2 --bridge-url http://localhost:3000
```

Esempio Linux/WSL:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM1 --room-id room2 --bridge-url http://localhost:3000
```

Firebase verra aggiornato in:

```text
rooms/room2
history/room2/<timestamp>
```

Nota: `COM3` e `COM4` sono solo esempi. Le porte corrette le trovi in Arduino IDE da `Tools > Port`.

## Due PC, un solo bridge

Se i due Arduino UNO sono collegati a due PC diversi, non devi per forza avviare due bridge.

La soluzione consigliata e usare:

```text
PC 1 = PC bridge centrale
PC 2 = PC secondario con Arduino collegato via USB
```

Il flusso diventa:

```text
Arduino Aula 1 -> USB -> PC 1 -> serial_to_bridge.py -> bridge PC 1 -> Firebase
Arduino Aula 2 -> USB -> PC 2 -> serial_to_bridge.py -> bridge PC 1 -> Firebase
```

Quindi:

- sul PC 1 avvii `bridge_server.py`;
- sul PC 1 avvii anche `serial_to_bridge.py` per `room1`;
- sul PC 2 avvii solo `serial_to_bridge.py` per `room2`;
- il PC 2 invia i dati al bridge del PC 1 usando l'IP del PC 1.

PC 1 e PC 2 devono essere collegati alla stessa rete Wi-Fi o LAN. Se sono su reti diverse, il PC 2 non riesce a raggiungere il bridge del PC 1.

### 1. Trovare l'IP del PC bridge

Sul PC che userai come bridge, devi trovare l'indirizzo IPv4 della scheda di rete.

#### Windows

Apri PowerShell o Prompt dei comandi e scrivi:

```powershell
ipconfig
```

Cerca la scheda Wi-Fi o Ethernet attiva e leggi:

```text
Indirizzo IPv4 . . . . . . . . . . . : 192.168.1.50
```

In questo esempio l'IP del PC bridge e:

```text
192.168.1.50
```

#### Linux

Puoi usare:

```bash
ip addr
```

Cerca l'interfaccia Wi-Fi o Ethernet attiva. Spesso si chiama `wlan0`, `wlp...`, `eth0` o `enp...`.

Esempio:

```text
inet 192.168.1.50/24
```

In alternativa puoi usare:

```bash
hostname -I
```

Il primo IP mostrato è spesso quello corretto della rete locale.

#### WSL

Se il bridge gira davvero dentro WSL, attenzione: l'IP di WSL non sempre coincide con l'IP del PC Windows.

Per una demo semplice, conviene avviare il bridge da Windows PowerShell, non dentro WSL, cosi gli altri PC possono raggiungerlo più facilmente usando l'IP Windows trovato con `ipconfig`.

Se vuoi comunque avviare il bridge dentro WSL, puoi vedere l'IP di WSL con:

```bash
hostname -I
```

Pero potresti dover configurare port forwarding o firewall di Windows. Per questo, nella demo risulta più semplice usare Python da Windows.

### 2. Avviare il bridge sul PC 1

Sul PC 1, cioè il PC bridge, avvia:

```powershell
py bridge\bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app
```

Oppure su Linux:

```bash
python3 bridge/bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app
```

Il bridge deve mostrare:

```text
Listening on http://0.0.0.0:3000
Initial study preference: balanced
Firebase preference path: settings/studyPreference
```

Questo significa che il bridge accetta connessioni non solo da `localhost`, ma anche dagli altri dispositivi della rete.

### 3. Testare il bridge dal PC 1

Sul PC 1 apri:

```text
http://localhost:3000/health
```

Risultato atteso:

```json
{"status":"ok","service":"smart-study-rooms-bridge"}
```

### 4. Testare il bridge dal PC 2

Sul PC 2 apri nel browser:

```text
http://IP_DEL_PC_1:3000/health
```

Esempio:

```text
http://192.168.1.50:3000/health
```

Se vedi la risposta `status: ok`, allora PC 2 riesce a raggiungere il bridge.

Se non funziona, controlla:

- PC 1 e PC 2 devono essere sulla stessa rete;
- il bridge deve essere acceso sul PC 1;
- Windows Firewall deve permettere a Python di ricevere connessioni sulla rete privata;
- l'IP usato deve essere quello corretto del PC 1.

### 5. Avviare Arduino Aula 1 sul PC 1

Sul PC 1, con Arduino Aula 1 collegato via USB:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room1 --bridge-url http://localhost:3000
```

Su Linux:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room1 --bridge-url http://localhost:3000
```

Questo aggiorna Firebase in:

```text
rooms/room1
history/room1/<timestamp>
```

### 6. Avviare Arduino Aula 2 sul PC 2

Sul PC 2, con Arduino Aula 2 collegato via USB, devi puntare al bridge del PC 1.

Esempio Windows:

```powershell
py bridge\serial_to_bridge.py --port COM3 --room-id room2 --bridge-url http://192.168.1.50:3000
```

Esempio Linux:

```bash
python3 bridge/serial_to_bridge.py --port /dev/ttyACM0 --room-id room2 --bridge-url http://192.168.1.50:3000
```

Sostituisci `192.168.1.50` con l'IP reale del PC 1.

Questo aggiorna Firebase in:

```text
rooms/room2
history/room2/<timestamp>
```

### Riassunto due PC

```text
PC 1:
  bridge_server.py --database-host TUO_DATABASE.firebasedatabase.app
  serial_to_bridge.py --port COM3 --room-id room1 --bridge-url http://localhost:3000

PC 2:
  serial_to_bridge.py --port COM3 --room-id room2 --bridge-url http://IP_DEL_PC_1:3000
```

In questo modo il progetto mantiene un'architettura pulita: un solo bridge centrale e due nodi sensore distribuiti.

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
predictions/room1
predictions/room2
```

Il nodo `actuators` non deve essere letto dall'app per accendere i LED: viene usato dal bridge e dagli script seriali.

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

Lo score viene calcolato lato Android, non su Arduino. Arduino invia solo i dati grezzi; app e bridge usano la stessa formula per ottenere risultati coerenti anche con il LED giallo dell'aula migliore.

Lo score finale va da 0 a 100 ed è una somma pesata di tre componenti:

```text
score = temperaturaComponent * pesoTemperatura
      + rumoreComponent * pesoRumore
      + umiditaComponent * pesoUmidita
```

Ogni componente viene prima normalizzata da 0 a 100:

```text
temperaturaComponent = 100 se la temperatura e tra 20 e 23 gradi
rumoreComponent      = 100 - noise
umiditaComponent     = 100 se l'umidita e tra 40% e 60%
```

Per temperatura e umidità, se il valore esce dal range ideale il punteggio scende gradualmente, non a scaglioni. Questo evita che due situazioni diverse vengano valutate allo stesso modo.

Pesi usati dalle preferenze:

```text
Bilanciata          -> temperatura 35%, rumore 40%, umidita 25%
Priorita silenzio   -> temperatura 10%, rumore 85%, umidita 5%
Priorita comfort    -> temperatura 55%, rumore 25%, umidita 20%
```

Nella preferenza `Priorita silenzio`, il rumore domina davvero la scelta. Per esempio, se Aula 1 ha `noise = 64` e Aula 2 ha `noise = 97`, Aula 1 ottiene molti piu punti sul rumore e viene preferita, salvo casi estremi sugli altri parametri.

Classificazione mostrata nell'app:

```text
score >= 80       -> Consigliata
score >= 60       -> Accettabile
score >= 40       -> Poco adatta
score < 40        -> Sconsigliata
```

La preferenza scelta dall'app viene salvata in Firebase:

```text
settings/studyPreference = balanced | quiet | comfort
```

Il bridge legge questo valore e usa la stessa preferenza per decidere quale LED giallo accendere.
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
presence: true/false
```

Se un dato è fuori dal range, il bridge risponde con errore `400` e non aggiorna Firebase.

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

Se il progetto è lento o Gradle genera problemi, aprilo da una cartella Windows locale invece che da WSL.

## Modalita di test consigliata

Per testare tutto senza sensori reali:

1. Imposta `USE_SIMULATION 1` su Arduino UNO n.1.
2. Imposta `USE_SIMULATION 1` su Arduino UNO n.2.
3. Avvia il bridge.
4. Avvia `serial_to_bridge.py` per `room1`.
5. Avvia `serial_to_bridge.py` per `room2`.
6. Controlla Firebase.
7. Apri app Android.

Se funziona, vedrai:

```text
rooms/room1 aggiornato dall'Arduino UNO n.1 via seriale
rooms/room2 aggiornato dall'Arduino UNO n.2 via seriale
history/room1 popolato
history/room2 popolato
app Android aggiornata in realtime
```

## Lettura e calibrazione del rumore

Il sensore KY-037 non restituisce direttamente i decibel. Nel progetto viene letto il pin analogico `AO` e Arduino calcola una stima del rumore su scala 0-100.

La logica nello sketch e questa:

```text
1. per 80 ms Arduino legge tanti campioni analogici da A1
2. trova il valore minimo e massimo della finestra
3. calcola peakToPeak = massimo - minimo
4. converte peakToPeak nella scala noise 0-100
5. durante i 10 secondi tra due invii conserva il picco piu alto
6. invia a Firebase solo il picco massimo degli ultimi 10 secondi
```

Quindi se parli forte per un istante durante quei 10 secondi, il sistema dovrebbe conservare il picco e inviarlo al giro successivo.

I parametri principali sono negli sketch Arduino:

```cpp
const unsigned long NOISE_SAMPLE_WINDOW_MS = 80;
const int NOISE_RAW_MIN = 0;
const int NOISE_RAW_MAX = 8;
```

`NOISE_RAW_MIN` indica sotto quale variazione il rumore viene considerato nullo. Con valore `0` la sensibilita è massima. `NOISE_RAW_MAX` indica quale variazione analogica corrisponde a 100/100. Con valore `8` anche variazioni piccole vengono amplificate molto.

Se il rumore resta spesso a 0 anche parlando vicino al sensore, prova questa procedura:

1. imposta temporaneamente nello sketch:

```cpp
#define NOISE_DEBUG 1
```

2. ricarica lo sketch su Arduino;
3. guarda nel terminale di `serial_to_bridge.py` il campo `noisePeak`;
4. parla vicino al sensore e osserva quanto sale `noisePeak`.

Esempio:

```json
{"name":"Aula 1","temperature":22.4,"humidity":48.0,"noise":17,"noisePeak":7}
```

Se `noisePeak` resta sempre 0 o 1, il problema è probabilmente hardware/cablaggio/sensibilità del modulo. Bisogna:

- usare il pin analogico `AO`, non `DO`;
- vedere se `AO` è collegato ad `A1`;
- vedere se `VCC` e `GND` sono corretti;
- vedere se il microfono è orientato correttamente;
- controllare l'eventuale trimmer del modulo, se presente;
- provare un altro sensore, perchè alcuni moduli economici hanno uscita analogica molto debole.

Se `noisePeak` sale ma `noise` resta troppo basso, abbassa ancora `NOISE_RAW_MAX`. Nel progetto è già impostato a `8`, quindi la sensibilità è molto alta. Puoi provare anche:

```cpp
const int NOISE_RAW_MAX = 5;
```

Se invece il rumore risulta troppo alto anche in silenzio, è normale: questa taratura privilegia la cattura di rumori piccoli tipici di un aula studio. Per ridurre i falsi positivi, alza `NOISE_RAW_MAX` oppure `NOISE_RAW_MIN`.

Quando hai finito la calibrazione, rimetti:

```cpp
#define NOISE_DEBUG 0
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

Il campo più importante è `target_score`: rappresenta lo score futuro dell'aula dopo un certo numero di minuti.

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

Il modello usato è:

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

Usi questo modo quando il database contiene già il nodo:

```text
history
```

In questo caso lo script scarica da solo lo storico da Firebase, allena il modello e salva le predizioni.

Schema:

```text
Firebase history -> predictor.py -> Firebase predictions -> app Android
```

Questo è il modo più comodo quando il bridge è già stato usato per un po' e ha popolato lo storico.

### Modo B: usare un JSON esportato manualmente da Firebase

Usi questo modo quando hai scaricato un file `.json` dalla console Firebase.

Schema:

```text
file JSON locale -> predictor.py -> terminale oppure Firebase predictions -> app Android
```

Questo è utile se vuoi fare prove offline, controllare il dataset o lavorare su uno storico esportato.

Se usi un JSON locale e vuoi anche vedere la predizione nell'app Android, devi comunque aggiungere `--database-host`, perchè senza quello lo script stampa solo il risultato nel terminale.

## Installazione dipendenze ML su Windows PowerShell

Apri PowerShell nella root del progetto.

Se il progetto Android è stato copiato in Windows ma il repository principale si trova su WSL, puoi usare una cartella Windows oppure aprire PowerShell nella cartella del repo se è accessibile.

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

Per `room1` è uguale, cambi solo file e room id:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\room1-export.json" --room-id room1 --export-csv dataset-room1.csv --horizon-minutes 1 --database-host TUO_DATABASE.firebasedatabase.app
```

Se invece hai esportato tutto il database oppure tutto il nodo `history`, `--room-id` non è necessario perchè dentro il JSON sono già presenti `room1` e `room2`.

Esempio:

```powershell
py lm\predictor.py --history-json "C:\Users\leonardo.levrini\Downloads\history-export.json" --export-csv dataset.csv --horizon-minutes 1 --database-host TUO_DATABASE.firebasedatabase.app
```

## Installazione dipendenze ML su WSL

Su Ubuntu/WSL recente potresti vedere questo errore se provi a usare `pip` globalmente:

```text
This environment is externally managed
```

E' normale. Significa che Ubuntu non vuole che tu installi pacchetti Python globali con `pip`. La soluzione corretta è usare un virtual environment dentro il progetto.

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

Quando è attivo vedrai il prefisso `(.venv)` nel terminale.

Installa le dipendenze ML:

```bash
pip install -r lm/requirements.txt
```

Da questo momento, finchè l'ambiente risulta attivo, usa `python` invece di `python3`:

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

`MAE` indica l'errore medio del modello. Più è basso, meglio e. Per esempio `MAE: 11.65` significa che in media il modello sbaglia di circa 11.65 punti sullo score.

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


