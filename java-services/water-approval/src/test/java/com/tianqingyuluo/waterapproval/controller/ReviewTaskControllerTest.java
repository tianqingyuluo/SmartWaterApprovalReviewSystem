package com.tianqingyuluo.waterapproval.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.ApplicantResultResponse;
import com.tianqingyuluo.waterapproval.dto.LoginRequest;
import com.tianqingyuluo.waterapproval.dto.MaterialPreviewResource;
import com.tianqingyuluo.waterapproval.dto.PendingTaskResponse;
import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerActionResponse;
import com.tianqingyuluo.waterapproval.dto.ReviewerActionSubmitRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerResultResponse;
import com.tianqingyuluo.waterapproval.dto.StatusUpdateRequest;
import com.tianqingyuluo.waterapproval.dto.SubmitResponse;
import com.tianqingyuluo.waterapproval.dto.TaskListResponse;
import com.tianqingyuluo.waterapproval.dto.TaskStatusResponse;
import com.tianqingyuluo.waterapproval.service.ReviewTaskService;
import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.io.ByteArrayInputStream;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ReviewTaskControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ReviewTaskService reviewTaskService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void getPendingTasksWithoutTokenShouldBeBlocked() throws Exception {
        mockMvc.perform(get("/task/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    void getPendingTasksWithTokenShouldSucceed() throws Exception {
        PendingTaskResponse task = new PendingTaskResponse();
        task.setTaskId("task-1");
        task.setSessionId("session-1");
        task.setStatus("QUEUED");
        when(reviewTaskService.getPendingTasks()).thenReturn(List.of(task));

        mockMvc.perform(get("/task/pending")
                        .header("X-Worker-Token", "test-worker-token"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].taskId").value("task-1"));
    }

    @Test
    void updateStatusWithoutTokenShouldBeBlocked() throws Exception {
        StatusUpdateRequest req = new StatusUpdateRequest();
        req.setStatus("PROCESSING");

        mockMvc.perform(put("/task/task-1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    void updateStatusWithValidTokenShouldSucceed() throws Exception {
        StatusUpdateRequest req = new StatusUpdateRequest();
        req.setStatus("PROCESSING");
        doNothing().when(reviewTaskService).updateStatus(eq("task-1"), eq("PROCESSING"));

        mockMvc.perform(put("/task/task-1/status")
                        .header("X-Worker-Token", "test-worker-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void writeResultWithoutTokenShouldBeBlocked() throws Exception {
        ResultWriteRequest req = new ResultWriteRequest();
        req.setStatus("COMPLETED");

        mockMvc.perform(put("/task/task-1/result")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    void updateStatusWithInvalidStatusShouldReturnError() throws Exception {
        StatusUpdateRequest req = new StatusUpdateRequest();
        req.setStatus("INVALID_STATUS");
        doThrow(new BusinessException(400, "无效的任务状态: INVALID_STATUS"))
                .when(reviewTaskService).updateStatus(eq("task-1"), eq("INVALID_STATUS"));

        mockMvc.perform(put("/task/task-1/status")
                        .header("X-Worker-Token", "test-worker-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(400));
    }

    @Test
    void updateStatusWithInvalidTransitionShouldReturnError() throws Exception {
        StatusUpdateRequest req = new StatusUpdateRequest();
        req.setStatus("COMPLETED");
        doThrow(new BusinessException(409, "不允许的状态流转: SUBMITTED -> COMPLETED"))
                .when(reviewTaskService).updateStatus(eq("task-1"), eq("COMPLETED"));

        mockMvc.perform(put("/task/task-1/status")
                        .header("X-Worker-Token", "test-worker-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(409));
    }

    @Test
    void getStatusWithValidSessionIdShouldSucceed() throws Exception {
        TaskStatusResponse resp = new TaskStatusResponse();
        resp.setTaskId("task-1");
        resp.setStatus("PROCESSING");
        when(reviewTaskService.getStatus(eq("task-1"), eq("session-1"), any())).thenReturn(resp);
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(get("/task/task-1/status")
                        .header("Authorization", "Bearer " + token)
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.status").value("PROCESSING"));
    }

    @Test
    void getApplicantResultWithSessionIdShouldSucceed() throws Exception {
        ApplicantResultResponse resp = new ApplicantResultResponse();
        resp.setTaskId("task-1");
        resp.setStatus("COMPLETED");
        when(reviewTaskService.getApplicantResult(eq("task-1"), eq("session-1"), any())).thenReturn(resp);
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(get("/task/task-1/result/applicant")
                        .header("Authorization", "Bearer " + token)
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void getReviewerResultWithSessionIdShouldSucceed() throws Exception {
        ReviewerResultResponse resp = new ReviewerResultResponse();
        resp.setTaskId("task-1");
        resp.setStatus("COMPLETED");
        resp.setManualReviewNotice("请人工复核证照一致性");
        when(reviewTaskService.getReviewerResult(eq("task-1"), eq("session-1"), any())).thenReturn(resp);
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(get("/task/task-1/result/reviewer")
                        .header("Authorization", "Bearer " + token)
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.manualReviewNotice").value("请人工复核证照一致性"));
    }

    @Test
    void previewMaterialWithoutLoginShouldBeRejected() throws Exception {
        mockMvc.perform(get("/task/task-1/material/BUSINESS_LICENSE/preview"))
                .andExpect(status().isUnauthorized())
                .andExpect(content().string("未登录或登录已过期"));
    }

    @Test
    void previewMaterialWithLoginShouldStreamInlineBinary() throws Exception {
        byte[] bytes = "image-bytes".getBytes();
        MaterialPreviewResource preview = new MaterialPreviewResource(
                new ByteArrayInputStream(bytes),
                "image/png",
                "营业执照.png",
                (long) bytes.length,
                "png"
        );
        when(reviewTaskService.previewMaterial(eq("task-1"), eq("BUSINESS_LICENSE"), any()))
                .thenReturn(preview);
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(get("/task/task-1/material/BUSINESS_LICENSE/preview")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(content().bytes(bytes))
                .andExpect(header().string("Content-Type", "image/png"))
                .andExpect(header().string("X-Content-Type-Options", "nosniff"))
                .andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("inline")));
    }

    @Test
    void previewMaterialBusinessErrorShouldUseHttpStatus() throws Exception {
        doThrow(new BusinessException(415, "当前材料格式暂不支持浏览器预览"))
                .when(reviewTaskService).previewMaterial(eq("task-1"), eq("APPLICATION_FORM"), any());
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(get("/task/task-1/material/APPLICATION_FORM/preview")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isUnsupportedMediaType())
                .andExpect(content().string("当前材料格式暂不支持浏览器预览"));
    }

    @Test
    void getTaskListShouldReturnTasksWithoutWorkerToken() throws Exception {
        TaskListResponse response = new TaskListResponse();
        response.setTotal(1);
        response.setPage(1);
        response.setSize(20);
        when(reviewTaskService.getTaskList(eq(1), eq(20), any())).thenReturn(response);
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(get("/task/list")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(1));
    }

    @Test
    void getTaskListShouldReturnPaginatedResults() throws Exception {
        TaskListResponse response = new TaskListResponse();
        response.setTotal(100);
        response.setPage(2);
        response.setSize(10);
        when(reviewTaskService.getTaskList(eq(2), eq(10), any())).thenReturn(response);
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(get("/task/list")
                        .header("Authorization", "Bearer " + token)
                        .param("page", "2")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.page").value(2))
                .andExpect(jsonPath("$.data.size").value(10));
    }

    @Test
    void getTaskListShouldCapMaxSize() throws Exception {
        TaskListResponse response = new TaskListResponse();
        response.setTotal(0);
        response.setPage(1);
        response.setSize(100);
        when(reviewTaskService.getTaskList(eq(1), eq(100), any())).thenReturn(response);
        String token = loginAs("admin", "admin123");

        mockMvc.perform(get("/task/list")
                        .header("Authorization", "Bearer " + token)
                        .param("size", "500"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void getTaskListShouldNormalizePageAndSizeLowerBounds() throws Exception {
        TaskListResponse response = new TaskListResponse();
        response.setTotal(0);
        response.setPage(1);
        response.setSize(1);
        when(reviewTaskService.getTaskList(eq(1), eq(1), any())).thenReturn(response);
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(get("/task/list")
                        .header("Authorization", "Bearer " + token)
                        .param("page", "0")
                        .param("size", "0"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.page").value(1))
                .andExpect(jsonPath("$.data.size").value(1));
    }

    @Test
    void resubmitCorrectionMaterialsShouldAcceptMultipartFiles() throws Exception {
        SubmitResponse response = new SubmitResponse();
        response.setTaskId("task-1");
        response.setStatus("PROCESSING");
        when(reviewTaskService.resubmitCorrectionMaterials(eq("task-1"), any(), any())).thenReturn(response);
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(multipart("/task/task-1/correction-materials")
                        .file("businessLicense", "new-license".getBytes())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.taskId").value("task-1"))
                .andExpect(jsonPath("$.data.status").value("PROCESSING"));
    }

    @Test
    void resubmitCorrectionMaterialsShouldReturnBusinessErrors() throws Exception {
        doThrow(new BusinessException(409, "当前任务不处于退回补正状态，不能补传材料"))
                .when(reviewTaskService).resubmitCorrectionMaterials(eq("task-1"), any(), any());
        String token = loginAs("applicant", "applicant123");

        mockMvc.perform(multipart("/task/task-1/correction-materials")
                        .file("applicationForm", "application".getBytes())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(409));
    }

    @Test
    void taskListWithoutLoginShouldBeRejected() throws Exception {
        mockMvc.perform(get("/task/list"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    void submitReviewerActionShouldSucceed() throws Exception {
        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("RETURN_FOR_CORRECTION");
        request.setReviewerRemark("请补充补正材料");

        ReviewerActionResponse response = new ReviewerActionResponse();
        response.setTaskId("task-1");
        response.setActionCode("RETURN_FOR_CORRECTION");
        response.setHandlingStatus("CORRECTION_REQUIRED");
        when(reviewTaskService.submitReviewerAction(eq("task-1"), any(), any())).thenReturn(response);

        String token = loginAs("reviewer", "reviewer123");
        mockMvc.perform(post("/task/task-1/reviewer-action")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.actionCode").value("RETURN_FOR_CORRECTION"))
                .andExpect(jsonPath("$.data.handlingStatus").value("CORRECTION_REQUIRED"));
    }

    @Test
    void submitReviewerActionShouldValidateRequestBody() throws Exception {
        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("   ");
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(post("/task/task-1/reviewer-action")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(400));
    }

    @Test
    void submitReviewerActionShouldReturnBusinessErrors() throws Exception {
        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("APPROVE_INITIAL_REVIEW");
        doThrow(new BusinessException(409, "该任务已提交过审核动作，不允许重复提交"))
                .when(reviewTaskService).submitReviewerAction(eq("task-1"), any(), any());
        String token = loginAs("reviewer", "reviewer123");

        mockMvc.perform(post("/task/task-1/reviewer-action")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(409));
    }

    private String loginAs(String username, String password) throws Exception {
        LoginRequest request = new LoginRequest();
        request.setUsername(username);
        request.setPassword(password);

        MvcResult result = mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andReturn();

        String body = result.getResponse().getContentAsString();
        return JsonPath.read(body, "$.data.token");
    }
}
