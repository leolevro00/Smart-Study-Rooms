package com.example.smartstudyrooms;

public final class RoomScoreCalculator {
    private RoomScoreCalculator() {
    }

    public enum StudyPreference {
        BALANCED("balanced", "Bilanciata", 35, 35, 20),
        QUIET("quiet", "Priorita silenzio", 20, 55, 15),
        THERMAL_COMFORT("comfort", "Priorita comfort", 50, 25, 20);


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

        int score = weightedScore(temperatureScore(room.getTemperature()), 35, preference.temperatureWeight)
                + weightedScore(noiseScore(room.getNoise()), 35, preference.noiseWeight)
                + weightedScore(humidityScore(room.getHumidity()), 20, preference.humidityWeight);


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
        if (noise <= 10) {
            return "Basso";
        }
        if (noise <= 20) {
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
        double clampedNoise = Math.max(0, Math.min(100, noise));
        return Math.round((float) (35 - (clampedNoise / 100.0) * 35));
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



    private static int weightedScore(int componentScore, int componentMax, int weight) {
        return Math.round((componentScore / (float) componentMax) * weight);
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
