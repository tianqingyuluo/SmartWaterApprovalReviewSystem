package com.tianqingyuluo.waterapproval.ai;

import com.sun.net.httpserver.HttpServer;
import com.tianqingyuluo.waterapproval.dto.AiReviewTaskRequest;
import com.tianqingyuluo.waterapproval.dto.AiReviewTaskResponse;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AiServiceClientTest {

    @Test
    void shouldDispatchReviewTaskWithInternalTokenAndCamelCasePayload() throws Exception {
        AtomicReference<String> token = new AtomicReference<>();
        AtomicReference<String> body = new AtomicReference<>();
        HttpServer server = startServer(202, "{\"aiTaskId\":\"task-1\",\"status\":\"QUEUED\",\"createdAt\":\"2026-05-27T01:00:00Z\"}", token, body);
        try {
            AiServiceClient client = new AiServiceClient(propertiesFor(server, "secret-token"));

            AiReviewTaskResponse response = client.dispatchReviewTask(request("task-1"));

            assertEquals("task-1", response.getAiTaskId());
            assertEquals("QUEUED", response.getStatus());
            assertEquals("secret-token", token.get());
            assertTrue(body.get().contains("\"taskId\":\"task-1\""));
            assertTrue(body.get().contains("\"materialType\":\"APPLICATION_FORM\""));
            assertTrue(body.get().contains("\"storageKey\":\"task-1/APPLICATION_FORM/app.pdf\""));
        } finally {
            server.stop(0);
        }
    }

    @Test
    void shouldMapPythonServerFailureToRetryableUpstreamError() throws Exception {
        HttpServer server = startServer(503, "{\"detail\":\"unavailable\"}", new AtomicReference<>(), new AtomicReference<>());
        try {
            AiServiceClient client = new AiServiceClient(propertiesFor(server, ""));

            AiReviewTaskDispatchException ex = assertThrows(
                    AiReviewTaskDispatchException.class,
                    () -> client.dispatchReviewTask(request("task-503"))
            );

            assertEquals("UPSTREAM_5XX", ex.getFailureCategory());
            assertEquals(503, ex.getStatusCode());
            assertTrue(ex.isRetryable());
        } finally {
            server.stop(0);
        }
    }

    private static HttpServer startServer(
            int status,
            String response,
            AtomicReference<String> token,
            AtomicReference<String> body) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/api/review/tasks", exchange -> {
            token.set(exchange.getRequestHeaders().getFirst("X-Internal-Token"));
            body.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(status, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.start();
        return server;
    }

    private static AiServiceProperties propertiesFor(HttpServer server, String token) {
        AiServiceProperties properties = new AiServiceProperties();
        properties.setBaseUrl("http://localhost:" + server.getAddress().getPort());
        properties.setInternalToken(token);
        properties.setTimeout(Duration.ofSeconds(1));
        properties.getReviewTask().setMaxAttempts(1);
        return properties;
    }

    private static AiReviewTaskRequest request(String taskId) {
        AiReviewTaskRequest.Material material = new AiReviewTaskRequest.Material();
        material.setMaterialType("APPLICATION_FORM");
        material.setOriginalFileName("app.pdf");
        material.setStorageKey(taskId + "/APPLICATION_FORM/app.pdf");
        material.setFileExtension("pdf");
        material.setUploaded(true);

        AiReviewTaskRequest request = new AiReviewTaskRequest();
        request.setTaskId(taskId);
        request.setSessionId("session-" + taskId);
        request.setIdempotencyKey(taskId);
        request.setMaterials(List.of(material));
        return request;
    }
}
