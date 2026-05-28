package com.tianqingyuluo.waterapproval.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jayway.jsonpath.JsonPath;
import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessFinding;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchResultItem;
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
    void postMcpKnowledgeSearchShouldProxyToolResult() throws Exception {
        AiMcpKnowledgeSearchRequest request = new AiMcpKnowledgeSearchRequest();
        request.setQuery("营业执照");
        request.setTopK(3);

        AiMcpKnowledgeSearchResultItem item = new AiMcpKnowledgeSearchResultItem();
        item.setRank(1);
        item.setSection("materialChecklist");
        item.setId("MAT_BUSINESS_LICENSE");
        item.setTitle("营业执照");
        item.setMaterialType("BUSINESS_LICENSE");
        item.setExcerpt("营业执照用于校验申请主体。");
        item.setScore(1.0);
        item.setSourceIds(List.of("SRC_SAMPLE_BUSINESS_LICENSE"));
        item.setSourceRefs(List.of("SRC_PROCESS_DOC"));
        item.setBasisRefs(List.of("BASIS_MATERIAL_INITIAL_LIST"));

        AiMcpKnowledgeSearchResponse response = new AiMcpKnowledgeSearchResponse();
        response.setQuery("营业执照");
        response.setRequestedTopK(3);
        response.setTopK(3);
        response.setTotal(1);
        response.setResults(List.of(item));
        response.setKnowledgePackVersion("water-permit-mvp-2026-04-27");
        when(aiOpsService.callKnowledgeSearch(request)).thenReturn(response);

        String token = loginAs("admin", "admin123");
        mockMvc.perform(post("/ai/mcp/knowledge-search")
                        .header("Authorization", "Bearer " + token)
                        .contentType(APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.query").value("营业执照"))
                .andExpect(jsonPath("$.data.results[0].id").value("MAT_BUSINESS_LICENSE"))
                .andExpect(jsonPath("$.data.results[0].sourceIds[0]").value("SRC_SAMPLE_BUSINESS_LICENSE"));
    }

    @Test
    void postMcpCheckCompletenessShouldProxyToolResult() throws Exception {
        AiMcpCompletenessRequest request = new AiMcpCompletenessRequest();
        request.setMaterials(List.of("APPLICATION_FORM", "BUSINESS_LICENSE"));

        AiMcpCompletenessFinding finding = new AiMcpCompletenessFinding();
        finding.setCode("MISSING_MATERIAL");
        finding.setSeverity("WARNING");
        finding.setMaterialType("ID_CARD");
        finding.setMaterialId("MAT_ID_CARD");
        finding.setMaterialDisplayName("法定代表人身份证");
        finding.setMessage("缺少法定代表人身份证。");
        finding.setApplicantMessage("请补充身份证。");
        finding.setBasisRefs(List.of("BASIS_MATERIAL_INITIAL_LIST"));
        finding.setSourceRefs(List.of("SRC_SAMPLE_ID_CARD"));

        AiMcpCompletenessResponse response = new AiMcpCompletenessResponse();
        response.setSubmitted(List.of("APPLICATION_FORM", "BUSINESS_LICENSE"));
        response.setRequired(List.of("APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"));
        response.setMissing(List.of("ID_CARD"));
        response.setComplete(false);
        response.setFindings(List.of(finding));
        response.setKnowledgePackVersion("water-permit-mvp-2026-04-27");
        when(aiOpsService.callCheckCompleteness(request)).thenReturn(response);

        String token = loginAs("admin", "admin123");
        mockMvc.perform(post("/ai/mcp/check-completeness")
                        .header("Authorization", "Bearer " + token)
                        .contentType(APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.complete").value(false))
                .andExpect(jsonPath("$.data.missing[0]").value("ID_CARD"))
                .andExpect(jsonPath("$.data.findings[0].code").value("MISSING_MATERIAL"));
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
