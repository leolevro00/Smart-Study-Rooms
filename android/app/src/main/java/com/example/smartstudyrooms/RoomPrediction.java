package com.example.smartstudyrooms;

public class RoomPrediction {
    private Long currentScore;
    private Long predictedScore;
    private Long horizonMinutes;
    private String trend;
    private String model;
    private Double mae;
    private Long generatedAt;

    public RoomPrediction() {
        // Required by Firebase Realtime Database.
    }

    public Long getCurrentScore() {
        return currentScore;
    }

    public void setCurrentScore(Long currentScore) {
        this.currentScore = currentScore;
    }

    public Long getPredictedScore() {
        return predictedScore;
    }

    public void setPredictedScore(Long predictedScore) {
        this.predictedScore = predictedScore;
    }

    public Long getHorizonMinutes() {
        return horizonMinutes;
    }

    public void setHorizonMinutes(Long horizonMinutes) {
        this.horizonMinutes = horizonMinutes;
    }

    public String getTrend() {
        return trend;
    }

    public void setTrend(String trend) {
        this.trend = trend;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public Double getMae() {
        return mae;
    }

    public void setMae(Double mae) {
        this.mae = mae;
    }

    public Long getGeneratedAt() {
        return generatedAt;
    }

    public void setGeneratedAt(Long generatedAt) {
        this.generatedAt = generatedAt;
    }
}
