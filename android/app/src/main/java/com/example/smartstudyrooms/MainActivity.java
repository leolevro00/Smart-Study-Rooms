package com.example.smartstudyrooms;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {
    private static final String NOISE_CHANNEL_ID = "noise_alerts";
    private static final int NOTIFICATION_PERMISSION_REQUEST_CODE = 20;
    private static final int NOISE_ALERT_THRESHOLD = 70;
    private static final int NOISE_ALERT_RESET_THRESHOLD = 60;

    private DatabaseReference roomsRef;
    private ValueEventListener roomsListener;

    private TextView connectionMessage;
    private TextView recommendedRoomText;

    private RoomViews room1Views;
    private RoomViews room2Views;

    private Room room1;
    private Room room2;
    private boolean room1NoiseAlertActive;
    private boolean room2NoiseAlertActive;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        bindViews();
        createNoiseNotificationChannel();
        requestNotificationPermissionIfNeeded();
        roomsRef = FirebaseDatabase.getInstance().getReference("rooms");
        listenForRooms();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (roomsRef != null && roomsListener != null) {
            roomsRef.removeEventListener(roomsListener);
        }
    }

    private void bindViews() {
        connectionMessage = findViewById(R.id.connectionMessage);
        recommendedRoomText = findViewById(R.id.recommendedRoomText);

        room1Views = new RoomViews(
                findViewById(R.id.room1Card),
                findViewById(R.id.room1Name),
                findViewById(R.id.room1Temperature),
                findViewById(R.id.room1TemperatureBar),
                findViewById(R.id.room1Humidity),
                findViewById(R.id.room1HumidityBar),
                findViewById(R.id.room1Noise),
                findViewById(R.id.room1NoiseBar),
                findViewById(R.id.room1Presence),
                findViewById(R.id.room1LastUpdate),
                findViewById(R.id.room1Score),
                findViewById(R.id.room1Status)
        );

        room2Views = new RoomViews(
                findViewById(R.id.room2Card),
                findViewById(R.id.room2Name),
                findViewById(R.id.room2Temperature),
                findViewById(R.id.room2TemperatureBar),
                findViewById(R.id.room2Humidity),
                findViewById(R.id.room2HumidityBar),
                findViewById(R.id.room2Noise),
                findViewById(R.id.room2NoiseBar),
                findViewById(R.id.room2Presence),
                findViewById(R.id.room2LastUpdate),
                findViewById(R.id.room2Score),
                findViewById(R.id.room2Status)
        );
    }

    private void listenForRooms() {
        showMessage("Connessione a Firebase in corso...");

        roomsListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot snapshot) {
                if (!snapshot.exists()) {
                    room1 = null;
                    room2 = null;
                    showMessage("Dati non disponibili. Invia dati dai nodi IoT o dal simulatore.");
                    clearRoom(room1Views, "Aula 1");
                    clearRoom(room2Views, "Aula 2");
                    updateRecommendation();
                    return;
                }

                room1 = snapshot.child("room1").getValue(Room.class);
                room2 = snapshot.child("room2").getValue(Room.class);

                if (room1 == null && room2 == null) {
                    showMessage("Dati non disponibili per le aule.");
                } else {
                    connectionMessage.setVisibility(View.GONE);
                }

                updateRoom(room1Views, room1, "Aula 1");
                updateRoom(room2Views, room2, "Aula 2");
                updateRecommendation();
                evaluateNoiseAlert("room1", room1, "Aula 1");
                evaluateNoiseAlert("room2", room2, "Aula 2");
            }

            @Override
            public void onCancelled(DatabaseError error) {
                showMessage("Errore Firebase: " + error.getMessage());
            }
        };

        roomsRef.addValueEventListener(roomsListener);
    }

    private void updateRoom(RoomViews views, Room room, String fallbackName) {
        if (room == null) {
            clearRoom(views, fallbackName);
            return;
        }

        int score = RoomScoreCalculator.calculateScore(room);
        String status = RoomScoreCalculator.getStatus(score);

        views.name.setText(valueOrFallback(room.getName(), fallbackName));
        views.temperature.setText("Temperatura: " + formatDecimal(room.getTemperature()) + " \u00B0C");
        views.humidity.setText("Umidita: " + formatDecimal(room.getHumidity()) + "%");
        views.noise.setText("Rumore: " + RoomScoreCalculator.getNoiseLabel(room.getNoise())
                + " (" + formatDecimal(room.getNoise()) + ")");
        views.temperatureBar.setProgress(progressValue(room.getTemperature(), 40));
        views.humidityBar.setProgress(progressValue(room.getHumidity(), 100));
        views.noiseBar.setProgress(progressValue(room.getNoise(), 100));
        views.presence.setText("Presenza: " + formatPresence(room.getPresence()));
        views.lastUpdate.setText("Ultimo aggiornamento: " + formatTimestamp(room.getLastUpdate()));
        views.score.setText("Score: " + score + "/100");
        views.status.setText("Stato: " + status);
        views.card.setCardBackgroundColor(getColorForStatus(status));
    }

    private void clearRoom(RoomViews views, String fallbackName) {
        views.name.setText(fallbackName);
        views.temperature.setText("Temperatura: N/D");
        views.humidity.setText("Umidita: N/D");
        views.noise.setText("Rumore: N/D");
        views.temperatureBar.setProgress(0);
        views.humidityBar.setProgress(0);
        views.noiseBar.setProgress(0);
        views.presence.setText("Presenza: N/D");
        views.lastUpdate.setText("Ultimo aggiornamento: N/D");
        views.score.setText("Score: N/D");
        views.status.setText("Stato: dati non disponibili");
        views.card.setCardBackgroundColor(getColor(R.color.card_neutral));
    }

    private void updateRecommendation() {
        if (room1 == null && room2 == null) {
            recommendedRoomText.setText("Aula consigliata: dati non disponibili");
            return;
        }

        if (room1 != null && room2 == null) {
            recommendedRoomText.setText("Aula consigliata: " + valueOrFallback(room1.getName(), "Aula 1"));
            return;
        }

        if (room1 == null) {
            recommendedRoomText.setText("Aula consigliata: " + valueOrFallback(room2.getName(), "Aula 2"));
            return;
        }

        int room1Score = RoomScoreCalculator.calculateScore(room1);
        int room2Score = RoomScoreCalculator.calculateScore(room2);

        if (room1Score == room2Score) {
            recommendedRoomText.setText("Aula consigliata: pari merito");
            return;
        }

        Room bestRoom = room1Score > room2Score ? room1 : room2;
        recommendedRoomText.setText("Aula consigliata: " + valueOrFallback(bestRoom.getName(), "Aula"));
    }

    private void evaluateNoiseAlert(String roomId, Room room, String fallbackName) {
        if (room == null || room.getNoise() == null) {
            setNoiseAlertActive(roomId, false);
            return;
        }

        double noise = room.getNoise();
        boolean alreadyNotified = isNoiseAlertActive(roomId);

        if (noise >= NOISE_ALERT_THRESHOLD && !alreadyNotified) {
            showNoiseNotification(roomId, valueOrFallback(room.getName(), fallbackName), noise);
            setNoiseAlertActive(roomId, true);
        } else if (noise <= NOISE_ALERT_RESET_THRESHOLD) {
            setNoiseAlertActive(roomId, false);
        }
    }

    private void showNoiseNotification(String roomId, String roomName, double noise) {
        if (!canPostNotifications()) {
            return;
        }

        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        int pendingIntentFlags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            pendingIntentFlags |= PendingIntent.FLAG_IMMUTABLE;
        }

        PendingIntent pendingIntent = PendingIntent.getActivity(
                this,
                roomId.hashCode(),
                intent,
                pendingIntentFlags
        );

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, NOISE_CHANNEL_ID)
                : new Notification.Builder(this);

        builder.setSmallIcon(R.drawable.ic_notification_noise)
                .setContentTitle("Rumore alto in " + roomName)
                .setContentText("Livello rilevato: " + formatDecimal(noise) + "/100.")
                .setContentIntent(pendingIntent)
                .setAutoCancel(true);

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            builder.setPriority(Notification.PRIORITY_HIGH);
        }

        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        notificationManager.notify(roomId.hashCode(), builder.build());
    }

    private void createNoiseNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }

        NotificationChannel channel = new NotificationChannel(
                NOISE_CHANNEL_ID,
                "Avvisi rumore",
                NotificationManager.IMPORTANCE_HIGH
        );
        channel.setDescription("Notifiche quando un'aula diventa troppo rumorosa");

        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        notificationManager.createNotificationChannel(channel);
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            return;
        }
        if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
            return;
        }

        requestPermissions(
                new String[]{Manifest.permission.POST_NOTIFICATIONS},
                NOTIFICATION_PERMISSION_REQUEST_CODE
        );
    }

    private boolean canPostNotifications() {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU
                || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private boolean isNoiseAlertActive(String roomId) {
        return "room1".equals(roomId) ? room1NoiseAlertActive : room2NoiseAlertActive;
    }

    private void setNoiseAlertActive(String roomId, boolean active) {
        if ("room1".equals(roomId)) {
            room1NoiseAlertActive = active;
        } else {
            room2NoiseAlertActive = active;
        }
    }

    private void showMessage(String message) {
        connectionMessage.setText(message);
        connectionMessage.setVisibility(View.VISIBLE);
    }

    private String formatDecimal(Double value) {
        if (value == null) {
            return "N/D";
        }
        return String.format(Locale.ITALY, "%.1f", value);
    }

    private String formatPresence(Boolean presence) {
        if (presence == null) {
            return "N/D";
        }
        return presence ? "Rilevata" : "Non rilevata";
    }

    private String formatTimestamp(Long timestamp) {
        if (timestamp == null || timestamp <= 0) {
            return "N/D";
        }

        long millis = timestamp < 10_000_000_000L ? timestamp * 1000L : timestamp;
        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.ITALY);
        return formatter.format(new Date(millis));
    }

    private int progressValue(Double value, int max) {
        if (value == null) {
            return 0;
        }
        return Math.max(0, Math.min(max, (int) Math.round(value)));
    }

    private String valueOrFallback(String value, String fallback) {
        if (value == null || value.trim().isEmpty()) {
            return fallback;
        }
        return value;
    }

    private int getColorForStatus(String status) {
        if ("Consigliata".equals(status)) {
            return getColor(R.color.status_recommended_bg);
        }
        if ("Accettabile".equals(status)) {
            return getColor(R.color.status_acceptable_bg);
        }
        if ("Poco adatta".equals(status)) {
            return getColor(R.color.status_low_bg);
        }
        return getColor(R.color.status_bad_bg);
    }

    private static class RoomViews {
        final CardView card;
        final TextView name;
        final TextView temperature;
        final ProgressBar temperatureBar;
        final TextView humidity;
        final ProgressBar humidityBar;
        final TextView noise;
        final ProgressBar noiseBar;
        final TextView presence;
        final TextView lastUpdate;
        final TextView score;
        final TextView status;

        RoomViews(
                CardView card,
                TextView name,
                TextView temperature,
                ProgressBar temperatureBar,
                TextView humidity,
                ProgressBar humidityBar,
                TextView noise,
                ProgressBar noiseBar,
                TextView presence,
                TextView lastUpdate,
                TextView score,
                TextView status
        ) {
            this.card = card;
            this.name = name;
            this.temperature = temperature;
            this.temperatureBar = temperatureBar;
            this.humidity = humidity;
            this.humidityBar = humidityBar;
            this.noise = noise;
            this.noiseBar = noiseBar;
            this.presence = presence;
            this.lastUpdate = lastUpdate;
            this.score = score;
            this.status = status;
        }
    }
}
