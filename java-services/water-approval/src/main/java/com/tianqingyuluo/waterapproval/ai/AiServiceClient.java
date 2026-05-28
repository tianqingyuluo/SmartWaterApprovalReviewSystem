package com.tianqingyuluo.waterapproval.ai;

import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchResponse;
import com.tianqingyuluo.waterapproval.dto.AiReviewTaskRequest;
import com.tianqingyuluo.waterapproval.dto.AiReviewTaskResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiServiceClient {

    public static final int RESPONSE_BODY_LIMIT = 500;

    private final AiServiceProperties properties;

    public boolean isReviewTaskDispatchEnabled() {
        return properties.getReviewTask().isEnabled();
    }

    public AiHealthResponse checkHealth() {
        AiHealthResponse response = baseHealthResponse();

        if (properties.normalizedBaseUrl().isBlank() || properties.normalizedHealthPath().isBlank()) {
            response.setMessage("AI service baseUrl or healthPath is not configured");
            return response;
        }

        try {
            ResponseEntity<String> entity = buildRestClient().get()
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

    public AiReviewTaskResponse dispatchReviewTask(AiReviewTaskRequest request) {
        if (!isReviewTaskDispatchEnabled()) {
            throw new AiReviewTaskDispatchException(
                    "AI review task dispatch is disabled",
                    "SYSTEM_ERROR",
                    false,
                    null,
                    null
            );
        }
        if (properties.normalizedBaseUrl().isBlank() || properties.normalizedReviewTaskPath().isBlank()) {
            throw new AiReviewTaskDispatchException(
                    "AI service baseUrl or reviewTask.path is not configured",
                    "SYSTEM_ERROR",
                    false,
                    null,
                    null
            );
        }

        AiReviewTaskDispatchException lastFailure = null;
        int attempts = properties.getReviewTask().safeMaxAttempts();
        for (int attempt = 1; attempt <= attempts; attempt++) {
            try {
                AiReviewTaskResponse response = buildRestClient().post()
                        .uri(properties.normalizedReviewTaskPath())
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON)
                        .body(request)
                        .retrieve()
                        .body(AiReviewTaskResponse.class);
                if (response == null || response.getAiTaskId() == null || response.getAiTaskId().isBlank()) {
                    throw new AiReviewTaskDispatchException(
                            "AI service returned an empty review task response",
                            "SCHEMA_MISMATCH",
                            false,
                            null,
                            null
                    );
                }
                log.info(
                        "AI review task dispatched: taskId={}, aiTaskId={}, status={}",
                        request.getTaskId(),
                        response.getAiTaskId(),
                        response.getStatus()
                );
                return response;
            } catch (RestClientResponseException e) {
                lastFailure = mapResponseFailure(e);
            } catch (ResourceAccessException e) {
                lastFailure = new AiReviewTaskDispatchException(
                        "AI service review task dispatch failed: " + e.getClass().getSimpleName(),
                        "TIMEOUT",
                        true,
                        null,
                        e
                );
            } catch (RestClientException e) {
                lastFailure = new AiReviewTaskDispatchException(
                        "AI service review task dispatch failed: " + e.getClass().getSimpleName(),
                        "SYSTEM_ERROR",
                        true,
                        null,
                        e
                );
            }

            log.warn(
                    "AI review task dispatch failed: taskId={}, attempt={}/{}, category={}, retryable={}, statusCode={}",
                    request.getTaskId(),
                    attempt,
                    attempts,
                    lastFailure.getFailureCategory(),
                    lastFailure.isRetryable(),
                    lastFailure.getStatusCode()
            );
            if (!lastFailure.isRetryable()) {
                break;
            }
        }

        throw lastFailure;
    }

    public AiMcpKnowledgeSearchResponse callKnowledgeSearch(AiMcpKnowledgeSearchRequest request) {
        if (properties.normalizedBaseUrl().isBlank() || properties.normalizedKnowledgeSearchPath().isBlank()) {
            throw new AiMcpToolCallException("AI MCP knowledge_search path is not configured", null, null);
        }
        try {
            AiMcpKnowledgeSearchResponse response = buildRestClient().post()
                    .uri(properties.normalizedKnowledgeSearchPath())
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(AiMcpKnowledgeSearchResponse.class);
            if (response == null || response.getResults() == null) {
                throw new AiMcpToolCallException("AI MCP knowledge_search returned an empty response", null, null);
            }
            log.info("AI MCP knowledge_search called: query={}, topK={}, total={}",
                    request.getQuery(), request.getTopK(), response.getTotal());
            return response;
        } catch (RestClientResponseException e) {
            throw mapMcpToolFailure("knowledge_search", e);
        } catch (RestClientException e) {
            throw new AiMcpToolCallException(
                    "AI MCP knowledge_search failed: " + e.getClass().getSimpleName(),
                    null,
                    e
            );
        }
    }

    public AiMcpCompletenessResponse callCheckCompleteness(AiMcpCompletenessRequest request) {
        if (properties.normalizedBaseUrl().isBlank() || properties.normalizedCheckCompletenessPath().isBlank()) {
            throw new AiMcpToolCallException("AI MCP check_completeness path is not configured", null, null);
        }
        try {
            AiMcpCompletenessResponse response = buildRestClient().post()
                    .uri(properties.normalizedCheckCompletenessPath())
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(AiMcpCompletenessResponse.class);
            if (response == null || response.getRequired() == null || response.getMissing() == null) {
                throw new AiMcpToolCallException("AI MCP check_completeness returned an empty response", null, null);
            }
            log.info("AI MCP check_completeness called: submitted={}, missing={}",
                    response.getSubmitted() == null ? 0 : response.getSubmitted().size(),
                    response.getMissing().size());
            return response;
        } catch (RestClientResponseException e) {
            throw mapMcpToolFailure("check_completeness", e);
        } catch (RestClientException e) {
            throw new AiMcpToolCallException(
                    "AI MCP check_completeness failed: " + e.getClass().getSimpleName(),
                    null,
                    e
            );
        }
    }

    private RestClient buildRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.getTimeout());
        requestFactory.setReadTimeout(properties.getTimeout());

        return RestClient.builder()
                .baseUrl(properties.normalizedBaseUrl())
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .requestFactory(requestFactory)
                .requestInterceptor((request, body, execution) -> {
                    if (properties.hasInternalToken()) {
                        request.getHeaders().set("X-Internal-Token", properties.getInternalToken());
                    }
                    return execution.execute(request, body);
                })
                .build();
    }

    private AiReviewTaskDispatchException mapResponseFailure(RestClientResponseException e) {
        int statusCode = e.getStatusCode().value();
        boolean retryable = statusCode == 408 || statusCode == 429 || statusCode >= 500;
        String category = switch (statusCode) {
            case 401, 403 -> "AUTH_ERROR";
            case 408 -> "TIMEOUT";
            case 429 -> "RATE_LIMIT";
            default -> statusCode >= 500 ? "UPSTREAM_5XX" : "SYSTEM_ERROR";
        };
        return new AiReviewTaskDispatchException(
                "AI service review task dispatch returned HTTP "
                        + statusCode
                        + ": "
                        + limitBody(e.getResponseBodyAsString()),
                category,
                retryable,
                statusCode,
                e
        );
    }

    private AiMcpToolCallException mapMcpToolFailure(String toolName, RestClientResponseException e) {
        int statusCode = e.getStatusCode().value();
        return new AiMcpToolCallException(
                "AI MCP " + toolName + " returned HTTP "
                        + statusCode
                        + ": "
                        + limitBody(e.getResponseBodyAsString()),
                statusCode,
                e
        );
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
        return body.length() <= RESPONSE_BODY_LIMIT ? body : body.substring(0, RESPONSE_BODY_LIMIT);
    }
}
