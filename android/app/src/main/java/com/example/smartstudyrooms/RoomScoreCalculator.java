package com.example.smartstudyrooms;

public final class RoomScoreCalculator {
    private RoomScoreCalculator() {
    }

    public static int calculateScore(Room room) {
        if (room == null) {
            return 0;
        }

        int score = temperatureScore(room.getTemperature())
                + noiseScore(room.getNoise())
                + humidityScore(room.getHumidity())
                + presenceScore(room.getPresence());

        return clamp(score, 0, 100);
    }

    public static String getStatus(int score) {
        if (score >= 80) {
            return "Consigliata";
        }
        if (score >= 60) {
            return "Accettabile";
        }
        if (score >= 40) {
            return "Poco adatta";
        }
        return "Sconsigliata";
    }

    public static String getNoiseLabel(Double noise) {
        if (noise == null) {
            return "N/D";
        }
        if (noise <= 40) {
            return "Basso";
        }
        if (noise <= 60) {
            return "Medio";
        }
        return "Alto";
    }

    private static int temperatureScore(Double temperature) {
        if (temperature == null) {
            return 0;
        }
        if (temperature >= 20 && temperature <= 23) {
            return 35;
        }
        if (temperature >= 18 && temperature <= 25) {
            return 25;
        }
        if (temperature >= 16 && temperature <= 28) {
            return 15;
        }
        return 5;
    }

    private static int noiseScore(Double noise) {
        if (noise == null) {
            return 0;
        }
        if (noise <= 40) {
            return 35;
        }
        if (noise <= 60) {
            return 22;
        }
        if (noise <= 75) {
            return 10;
        }
        return 3;
    }

    private static int humidityScore(Double humidity) {
        if (humidity == null) {
            return 0;
        }
        if (humidity >= 40 && humidity <= 60) {
            return 20;
        }
        if (humidity >= 30 && humidity <= 70) {
            return 12;
        }
        return 5;
    }

    private static int presenceScore(Boolean presence) {
        if (presence == null) {
            return 5;
        }
        return presence ? 5 : 10;
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
