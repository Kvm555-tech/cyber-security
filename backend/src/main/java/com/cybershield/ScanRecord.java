package com.cybershield;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "scans")
public class ScanRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, columnDefinition = "text")
    private String url;

    @Column(nullable = false)
    private String prediction;

    @Column(nullable = false)
    private double threatScore;

    @Column(nullable = false)
    private String threatLevel;

    @Column(nullable = false)
    private double modelScore;

    @Column(nullable = false)
    private double ruleScore;

    @Column(nullable = false, columnDefinition = "text")
    private String reasonsJson;

    @Column(nullable = false)
    private Instant scannedAt;

    protected ScanRecord() {
    }

    public ScanRecord(String url, String prediction, double threatScore, String threatLevel,
                      double modelScore, double ruleScore, String reasonsJson) {
        this.url = url;
        this.prediction = prediction;
        this.threatScore = threatScore;
        this.threatLevel = threatLevel;
        this.modelScore = modelScore;
        this.ruleScore = ruleScore;
        this.reasonsJson = reasonsJson;
        this.scannedAt = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public String getUrl() {
        return url;
    }

    public String getPrediction() {
        return prediction;
    }

    public double getThreatScore() {
        return threatScore;
    }

    public String getThreatLevel() {
        return threatLevel;
    }

    public double getModelScore() {
        return modelScore;
    }

    public double getRuleScore() {
        return ruleScore;
    }

    public String getReasonsJson() {
        return reasonsJson;
    }

    public Instant getScannedAt() {
        return scannedAt;
    }
}
