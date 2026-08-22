package com.example.smartstudyrooms;

public final class RoomScoreCalculator {
    private RoomScoreCalculator() {
    }

    public enum StudyPreference {
        BALANCED("balanced", "Bilanciata", 35, 40, 25),
        QUIET("quiet", "Priorita silenzio", 10, 85, 5),
        THERMAL_COMFORT("comfort", "Priorita comfort", 55, 25, 20);

        private final String firebaseKey;
        private final String label;
        private final int temperatureWeight;
        private final int noiseWeight;
        private final int humidityWeight;

        StudyPreference(
                String firebaseKey,
                String label,
                int temperatureWeight,
                int noiseWeight,
                int humidityWeight
        ) {
            this.firebaseKey = firebaseKey;
            this.label = label;
            this.temperatureWeight = temperatureWeight;
            this.noiseWeight = noiseWeight;
            this.humidityWeight = humidityWeight;
        }

        public String getLabel() {
            return label;
        }

        public String getFirebaseKey() {
            return firebaseKey;
        }
    }

    public static int calculateScore(Room room) {
        return calculateScore(room, StudyPreference.BALANCED);
    }

    public static int calculateScore(Room room, StudyPreference preference) {
        if (room == null) {
            return 0;
        }
        if (preference == null) {
            preference = StudyPreference.BALANCED;
        }

        double score = weightedScore(temperatureScore(room.getTemperature()), preference.temperatureWeight)
                + weightedScore(noiseScore(room.getNoise()), preference.noiseWeight)
                + weightedScore(humidityScore(room.getHumidity()), preference.humidityWeight);

        return clamp((int) Math.round(score), 0, 100);
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
        if (noise <= 35) {
            return "Basso";
        }
        if (noise <= 65) {
            return "Medio";
        }
        return "Alto";
    }

    private static double temperatureScore(Double temperature) {
        if (temperature == null) {
            return 0;
        }
        double value = temperature;
        if (value >= 20 && value <= 23) {
            return 100;
        }
        if (value < 20) {
            return linearScore(value, 16, 20);
        }
        return linearScore(value, 30, 23);
    }

    private static double noiseScore(Double noise) {
        if (noise == null) {
            return 0;
        }
        return 100 - clamp(noise, 0, 100);
    }

    private static double humidityScore(Double humidity) {
        if (humidity == null) {
            return 0;
        }
        double value = humidity;
        if (value >= 40 && value <= 60) {
            return 100;
        }
        if (value < 40) {
            return linearScore(value, 20, 40);
        }
        return linearScore(value, 80, 60);
    }

    private static double linearScore(double value, double zeroPoint, double fullPoint) {
        double score = ((value - zeroPoint) / (fullPoint - zeroPoint)) * 100;
        return clamp(score, 0, 100);
    }

    private static double weightedScore(double componentScore, int weight) {
        return componentScore * weight / 100.0;
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }
}