package com.cybershield;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ScanController {

    private final ScanRepository repository;
    private final ObjectMapper mapper;
    private final RestClient mlClient;

    public ScanController(ScanRepository repository, ObjectMapper mapper,
                          @Value("${ml.service.url}") String mlServiceUrl) {
        this.repository = repository;
        this.mapper = mapper;
        this.mlClient = RestClient.builder()
                .baseUrl(mlServiceUrl)
                .requestFactory(new SimpleClientHttpRequestFactory())
                .build();
    }

    public record ScanRequest(String url) {
    }

    @PostMapping("/scan")
    public ResponseEntity<?> scan(@RequestBody ScanRequest request) throws JsonProcessingException {

        JsonNode result;

        try {
            result = mlClient.post()
                    .uri("/scan")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of("url", request.url() == null ? "" : request.url()))
                    .retrieve()
                    .body(JsonNode.class);

        } catch (HttpClientErrorException.BadRequest error) {
            JsonNode body = mapper.readTree(error.getResponseBodyAsString());
            return ResponseEntity.badRequest().body(Map.of("error", body.path("error").asText()));

        } catch (ResourceAccessException error) {
            return ResponseEntity.status(503).body(Map.of(
                    "error", "The ML service is not running. Start it and try again."));
        }

        ScanRecord saved = repository.save(new ScanRecord(
                result.path("url").asText(),
                result.path("prediction").asText(),
                result.path("threatScore").asDouble(),
                result.path("threatLevel").asText(),
                result.path("modelScore").asDouble(),
                result.path("ruleScore").asDouble(),
                mapper.writeValueAsString(result.path("reasons"))));

        return ResponseEntity.ok(toResponse(saved));
    }

    @GetMapping("/history")
    public List<Map<String, Object>> history() throws JsonProcessingException {

        List<Map<String, Object>> rows = new java.util.ArrayList<>();

        for (ScanRecord record : repository.findTop20ByOrderByScannedAtDesc()) {
            rows.add(toResponse(record));
        }

        return rows;
    }

    @GetMapping("/stats")
    public Map<String, Long> stats() {
        return Map.of(
                "total", repository.count(),
                "legitimate", repository.countByPrediction("LEGITIMATE"),
                "suspicious", repository.countByPrediction("SUSPICIOUS"),
                "phishing", repository.countByPrediction("PHISHING"));
    }

    private Map<String, Object> toResponse(ScanRecord record) throws JsonProcessingException {
        return Map.of(
                "id", record.getId(),
                "url", record.getUrl(),
                "prediction", record.getPrediction(),
                "threatScore", record.getThreatScore(),
                "threatLevel", record.getThreatLevel(),
                "modelScore", record.getModelScore(),
                "ruleScore", record.getRuleScore(),
                "reasons", mapper.readTree(record.getReasonsJson()),
                "scannedAt", record.getScannedAt().toString());
    }
}
