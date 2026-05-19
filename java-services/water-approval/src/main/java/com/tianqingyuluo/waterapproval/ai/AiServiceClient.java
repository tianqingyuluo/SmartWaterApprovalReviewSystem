package com.tianqingyuluo.waterapproval.ai;

import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiServiceClient {

    private final AiServiceProperties properties;

    public AiHealthResponse checkHealth() {
        AiHealthResponse response = baseHealthResponse();

        if (properties.normalizedBaseUrl().isBlank() || properties.normalizedHealthPath().isBlank()) {
            response.setMessage("AI service baseUrl or healthPath is not configured");
            return response;
        }

        try {
            SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
            requestFactory.setConnectTimeout(properties.getTimeout());
            requestFactory.setReadTimeout(properties.getTimeout());

            RestClient restClient = RestClient.builder()
                    .baseUrl(properties.normalizedBaseUrl())
                    .defaultHeader(HttpHeaders.ACCEPT, "application/json")
                    .requestFactory(requestFactory)
                    .requestInterceptor((request, body, execution) -> {
                        if (properties.hasInternalToken()) {
                            request.getHeaders().set("X-Internal-Token", properties.getInternalToken());
                        }
                        return execution.execute(request, body);
                    })
                    .build();

            ResponseEntity<String> entity = restClient.get()
                    .uri(properties.normalizedHealthPath())
                    .retrieve()
                    .toEntity(String.class);

            response.setReachable(true);
            response.setStatusCode(entity.getStatusCode().value());
            response.setMessage("AI service health endpoint is reachable");
            response.setResponseBody(limitBody(entity.getBody()));
        } catch (RestClientResponseException e) {
            response.setStatusCode(e.getStatusCode().value());
            response.setMessage("AI service health endpoint returned HTTP " + e.getStatusCode().value());
            response.setResponseBody(limitBody(e.getResponseBodyAsString()));
            log.warn("AI service health endpoint returned non-success status: status={}", e.getStatusCode().value());
        } catch (RestClientException e) {
            response.setMessage("AI service health endpoint is unreachable: " + e.getClass().getSimpleName());
            log.warn("AI service health check failed: {}", e.getMessage());
        }

        return response;
    }

    private AiHealthResponse baseHealthResponse() {
        AiHealthResponse response = new AiHealthResponse();
        response.setBaseUrl(properties.normalizedBaseUrl());
        response.setHealthUrl(properties.healthUrl());
        response.setReachable(false);
        response.setStatusCode(null);
        response.setMessage("AI service health endpoint has not been checked");
        response.setResponseBody(null);
        response.setMcpTransport(properties.getMcpTransport());
        response.setMcpUrl(properties.mcpUrl());
        response.setInternalTokenConfigured(properties.hasInternalToken());
        response.setCheckedAt(LocalDateTime.now());
        return response;
    }

    private String limitBody(String body) {
        if (body == null || body.isBlank()) {
            return "";
        }
        return body.length() <= 500 ? body : body.substring(0, 500);
    }
}
