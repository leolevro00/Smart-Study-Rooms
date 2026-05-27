package com.example.smartstudyrooms;

public class Room {
    private String name;
    private Double temperature;
    private Double humidity;
    private Double noise;
    private Boolean presence;
    private Long lastUpdate;

    public Room() {
        // Required by Firebase Realtime Database.
    }

    public Room(String name, Double temperature, Double humidity, Double noise, Boolean presence, Long lastUpdate) {
        this.name = name;
        this.temperature = temperature;
        this.humidity = humidity;
        this.noise = noise;
        this.presence = presence;
        this.lastUpdate = lastUpdate;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Double getTemperature() {
        return temperature;
    }

    public void setTemperature(Double temperature) {
        this.temperature = temperature;
    }

    public Double getHumidity() {
        return humidity;
    }

    public void setHumidity(Double humidity) {
        this.humidity = humidity;
    }

    public Double getNoise() {
        return noise;
    }

    public void setNoise(Double noise) {
        this.noise = noise;
    }

    public Boolean getPresence() {
        return presence;
    }

    public void setPresence(Boolean presence) {
        this.presence = presence;
    }

    public Long getLastUpdate() {
        return lastUpdate;
    }

    public void setLastUpdate(Long lastUpdate) {
        this.lastUpdate = lastUpdate;
    }
}
