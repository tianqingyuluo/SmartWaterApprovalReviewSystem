package com.tianqingyuluo.waterapproval.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.dto.*;
import com.tianqingyuluo.waterapproval.service.ReviewTaskService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

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
        doThrow(new IllegalArgumentException("无效的任务状态: INVALID_STATUS"))
                .when(reviewTaskService).updateStatus(eq("task-1"), eq("INVALID_STATUS"));

        mockMvc.perform(put("/task/task-1/status")
                        .header("X-Worker-Token", "test-worker-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(500));
    }

    @Test
    void updateStatusWithInvalidTransitionShouldReturnError() throws Exception {
        StatusUpdateRequest req = new StatusUpdateRequest();
        req.setStatus("COMPLETED");
        doThrow(new IllegalArgumentException("不允许的状态流转: SUBMITTED -> COMPLETED"))
                .when(reviewTaskService).updateStatus(eq("task-1"), eq("COMPLETED"));

        mockMvc.perform(put("/task/task-1/status")
                        .header("X-Worker-Token", "test-worker-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(500));
    }

    @Test
    void getStatusWithValidSessionIdShouldSucceed() throws Exception {
        TaskStatusResponse resp = new TaskStatusResponse();
        resp.setTaskId("task-1");
        resp.setStatus("PROCESSING");
        when(reviewTaskService.getStatus("task-1", "session-1")).thenReturn(resp);

        mockMvc.perform(get("/task/task-1/status")
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
        when(reviewTaskService.getApplicantResult("task-1", "session-1")).thenReturn(resp);

        mockMvc.perform(get("/task/task-1/result/applicant")
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void getReviewerResultWithSessionIdShouldSucceed() throws Exception {
        ReviewerResultResponse resp = new ReviewerResultResponse();
        resp.setTaskId("task-1");
        resp.setStatus("COMPLETED");
        when(reviewTaskService.getReviewerResult("task-1", "session-1")).thenReturn(resp);

        mockMvc.perform(get("/task/task-1/result/reviewer")
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
