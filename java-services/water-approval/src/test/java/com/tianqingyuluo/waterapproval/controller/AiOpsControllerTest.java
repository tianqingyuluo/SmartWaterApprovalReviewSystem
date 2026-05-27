package com.tianqingyuluo.waterapproval.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jayway.jsonpath.JsonPath;
import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import com.tianqingyuluo.waterapproval.dto.LoginRequest;
import com.tianqingyuluo.waterapproval.service.AiOpsService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AiOpsControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AiOpsService aiOpsService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void getAiHealthShouldExposeConfiguredPythonStatus() throws Exception {
        AiHealthResponse response = new AiHealthResponse();
        response.setBaseUrl("http://localhost:8000");
        response.setHealthUrl("http://localhost:8000/health");
        response.setReachable(true);
        response.setStatusCode(200);
        response.setMessage("AI service health endpoint is reachable");
        response.setMcpTransport("streamable-http");
        response.setMcpUrl("http://localhost:8000/mcp");
        response.setInternalTokenConfigured(true);
        response.setCheckedAt(LocalDateTime.of(2026, 5, 19, 16, 0));
        when(aiOpsService.getHealth()).thenReturn(response);

        String token = loginAs("admin", "admin123");
        mockMvc.perform(get("/ai/health").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.baseUrl").value("http://localhost:8000"))
                .andExpect(jsonPath("$.data.healthUrl").value("http://localhost:8000/health"))
                .andExpect(jsonPath("$.data.reachable").value(true))
                .andExpect(jsonPath("$.data.mcpTransport").value("streamable-http"))
                .andExpect(jsonPath("$.data.internalTokenConfigured").value(true));
    }

    @Test
    void postAiIngestShouldReturnOpsCommandContract() throws Exception {
        AiIngestOperationResponse response = new AiIngestOperationResponse();
        response.setMode("ops-command");
        response.setWorkdir("../../python-services/smart-water-approval-review-system-py");
        response.setSourceDir("../../docs/参考资料");
        response.setChunkSize(512);
        response.setChunkOverlap(64);
        response.setRebuild(true);
        response.setCommand(List.of(
                "uv", "run", "python", "-m", "src.ingest.cli",
                "--source-dir", "../../docs/参考资料",
                "--chunk-size", "512",
                "--chunk-overlap", "64",
                "--rebuild"
        ));
        response.setVerificationCommand("uv run python -m src.mcp_server.demo --run-samples");
        response.setNote("Python 当前提供 ingest CLI 和 MCP 原生 transport；Java 侧输出可复现运维命令，不伪造 REST ingest。");
        when(aiOpsService.getIngestOperation()).thenReturn(response);

        String token = loginAs("admin", "admin123");
        mockMvc.perform(post("/ai/ingest").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.mode").value("ops-command"))
                .andExpect(jsonPath("$.data.command[0]").value("uv"))
                .andExpect(jsonPath("$.data.command[3]").value("-m"))
                .andExpect(jsonPath("$.data.command[4]").value("src.ingest.cli"))
                .andExpect(jsonPath("$.data.verificationCommand").value("uv run python -m src.mcp_server.demo --run-samples"));
    }

    @Test
    void aiHealthWithoutLoginShouldBeRejected() throws Exception {
        mockMvc.perform(get("/ai/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(401));
    }

    private String loginAs(String username, String password) throws Exception {
        LoginRequest request = new LoginRequest();
        request.setUsername(username);
        request.setPassword(password);

        MvcResult result = mockMvc.perform(post("/auth/login")
                        .contentType(APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andReturn();

        return JsonPath.read(result.getResponse().getContentAsString(), "$.data.token");
    }
}
