package com.tianqingyuluo.waterapproval.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.ApplicantResultResponse;
import com.tianqingyuluo.waterapproval.dto.PendingTaskResponse;
import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerResultResponse;
import com.tianqingyuluo.waterapproval.dto.StatusUpdateRequest;
import com.tianqingyuluo.waterapproval.dto.TaskListResponse;
import com.tianqingyuluo.waterapproval.dto.TaskStatusResponse;
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

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
        resp.setManualReviewNotice("请人工复核证照一致性");
        when(reviewTaskService.getReviewerResult("task-1", "session-1")).thenReturn(resp);

        mockMvc.perform(get("/task/task-1/result/reviewer")
                        .param("sessionId", "session-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.manualReviewNotice").value("请人工复核证照一致性"));
    }

    @Test
    void getTaskListShouldReturnTasksWithoutWorkerToken() throws Exception {
        TaskListResponse response = new TaskListResponse();
        response.setTotal(1);
        response.setPage(1);
        response.setSize(20);
        when(reviewTaskService.getTaskList(1, 20)).thenReturn(response);

        mockMvc.perform(get("/task/list"))
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
        when(reviewTaskService.getTaskList(2, 10)).thenReturn(response);

        mockMvc.perform(get("/task/list")
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
        when(reviewTaskService.getTaskList(1, 100)).thenReturn(response);

        mockMvc.perform(get("/task/list")
                        .param("size", "500"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
