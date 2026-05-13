package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.dto.TaskListResponse;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@ActiveProfiles("test")
class ReviewTaskServiceImplTest {

    @Autowired
    private ReviewTaskService reviewTaskService;

    @Autowired
    private ReviewTaskMapper taskMapper;

    @Test
    void writeResultShouldPersistKnowledgePackVersion() {
        ReviewTask task = new ReviewTask();
        task.setTaskId("task-kp-version");
        task.setSessionId("session-kp-version");
        task.setStatus("PROCESSING");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        ResultWriteRequest request = new ResultWriteRequest();
        request.setStatus("COMPLETED");
        request.setKnowledgePackVersion("water-permit-mvp-2026-04-27");

        reviewTaskService.writeResult("task-kp-version", request);

        ReviewTask updated = taskMapper.selectById(task.getId());
        assertEquals("COMPLETED", updated.getStatus());
        assertEquals("water-permit-mvp-2026-04-27", updated.getKnowledgePackVersion());
    }

    @Test
    void getTaskListShouldReturnTasksInDescOrder() {
        ReviewTask task1 = new ReviewTask();
        task1.setTaskId("task-list-1-" + System.currentTimeMillis());
        task1.setSessionId("session-list-1");
        task1.setStatus("SUBMITTED");
        task1.setSubmittedAt(LocalDateTime.now().minusDays(2));
        task1.setCreatedAt(LocalDateTime.now().minusDays(2));
        task1.setUpdatedAt(LocalDateTime.now().minusDays(2));
        taskMapper.insert(task1);

        ReviewTask task2 = new ReviewTask();
        task2.setTaskId("task-list-2-" + System.currentTimeMillis());
        task2.setSessionId("session-list-2");
        task2.setStatus("COMPLETED");
        task2.setSubmittedAt(LocalDateTime.now().minusDays(1));
        task2.setCreatedAt(LocalDateTime.now().minusDays(1));
        task2.setUpdatedAt(LocalDateTime.now().minusDays(1));
        taskMapper.insert(task2);

        TaskListResponse response = reviewTaskService.getTaskList(1, 20);

        assertNotNull(response);
        assertTrue(response.getTotal() >= 2);
        assertTrue(response.getItems().size() >= 2);

        int idx1 = -1, idx2 = -1;
        for (int i = 0; i < response.getItems().size(); i++) {
            if (response.getItems().get(i).getTaskId().equals(task2.getTaskId())) idx2 = i;
            if (response.getItems().get(i).getTaskId().equals(task1.getTaskId())) idx1 = i;
        }
        assertTrue(idx2 >= 0, "task2 should be in results");
        assertTrue(idx1 >= 0, "task1 should be in results");
        assertTrue(idx2 < idx1, "newer task should appear before older task");
    }

    @Test
    void getTaskListShouldNotChangeTaskStatus() {
        ReviewTask task = new ReviewTask();
        task.setTaskId("task-list-status");
        task.setSessionId("session-list-status");
        task.setStatus("QUEUED");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        reviewTaskService.getTaskList(1, 20);

        ReviewTask after = taskMapper.selectById(task.getId());
        assertEquals("QUEUED", after.getStatus());
    }

    @Test
    void getTaskListShouldRespectPagination() {
        long beforeCount = taskMapper.selectCount(null);

        for (int i = 0; i < 5; i++) {
            ReviewTask task = new ReviewTask();
            task.setTaskId("task-page-" + i + "-" + System.currentTimeMillis());
            task.setSessionId("session-page-" + i);
            task.setStatus("SUBMITTED");
            task.setSubmittedAt(LocalDateTime.now().minusMinutes(i));
            task.setCreatedAt(LocalDateTime.now().minusMinutes(i));
            task.setUpdatedAt(LocalDateTime.now().minusMinutes(i));
            taskMapper.insert(task);
        }

        TaskListResponse page1 = reviewTaskService.getTaskList(1, 2);
        assertEquals(beforeCount + 5, page1.getTotal());
        assertTrue(page1.getItems().size() <= 2);

        TaskListResponse page2 = reviewTaskService.getTaskList(2, 2);
        assertTrue(page2.getItems().size() <= 2);

        // Verify total count is consistent across pages
        TaskListResponse page3 = reviewTaskService.getTaskList(3, 2);
        assertEquals(page1.getTotal(), page3.getTotal());
    }
}
