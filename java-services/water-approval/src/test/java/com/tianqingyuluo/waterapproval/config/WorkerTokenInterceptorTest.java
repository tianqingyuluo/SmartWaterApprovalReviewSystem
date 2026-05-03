package com.tianqingyuluo.waterapproval.config;

import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.controller.WorkerApi;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.method.HandlerMethod;

import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class WorkerTokenInterceptorTest {

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    private WorkerTokenInterceptor interceptor;

    @BeforeEach
    void setUp() {
        interceptor = new WorkerTokenInterceptor();
        ReflectionTestUtils.setField(interceptor, "workerToken", "test-token");
    }

    @Test
    void shouldAllowNonHandlerMethodRequests() {
        assertTrue(interceptor.preHandle(request, response, "not-a-handler"));
    }

    @Test
    void shouldAllowRequestsWithoutWorkerApiAnnotation() throws NoSuchMethodException {
        Method method = NonWorkerController.class.getMethod("publicEndpoint");
        HandlerMethod handler = new HandlerMethod(new NonWorkerController(), method);

        assertTrue(interceptor.preHandle(request, response, handler));
    }

    @Test
    void shouldBlockWhenTokenNotConfigured() throws NoSuchMethodException {
        interceptor = new WorkerTokenInterceptor();
        ReflectionTestUtils.setField(interceptor, "workerToken", "");

        Method method = WorkerController.class.getMethod("workerEndpoint");
        HandlerMethod handler = new HandlerMethod(new WorkerController(), method);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> interceptor.preHandle(request, response, handler));
        assertEquals(403, ex.getCode());
        assertTrue(ex.getMessage().contains("token not configured"));
    }

    @Test
    void shouldBlockWhenTokenNull() throws NoSuchMethodException {
        interceptor = new WorkerTokenInterceptor();
        ReflectionTestUtils.setField(interceptor, "workerToken", null);

        Method method = WorkerController.class.getMethod("workerEndpoint");
        HandlerMethod handler = new HandlerMethod(new WorkerController(), method);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> interceptor.preHandle(request, response, handler));
        assertEquals(403, ex.getCode());
    }

    @Test
    void shouldAllowWhenTokenMatches() throws NoSuchMethodException {
        when(request.getHeader("X-Worker-Token")).thenReturn("test-token");

        Method method = WorkerController.class.getMethod("workerEndpoint");
        HandlerMethod handler = new HandlerMethod(new WorkerController(), method);

        assertTrue(interceptor.preHandle(request, response, handler));
    }

    @Test
    void shouldBlockWhenTokenDoesNotMatch() throws NoSuchMethodException {
        when(request.getHeader("X-Worker-Token")).thenReturn("wrong-token");

        Method method = WorkerController.class.getMethod("workerEndpoint");
        HandlerMethod handler = new HandlerMethod(new WorkerController(), method);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> interceptor.preHandle(request, response, handler));
        assertEquals(403, ex.getCode());
        assertTrue(ex.getMessage().contains("Invalid worker token"));
    }

    @Test
    void shouldBlockWhenTokenHeaderMissing() throws NoSuchMethodException {
        when(request.getHeader("X-Worker-Token")).thenReturn(null);

        Method method = WorkerController.class.getMethod("workerEndpoint");
        HandlerMethod handler = new HandlerMethod(new WorkerController(), method);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> interceptor.preHandle(request, response, handler));
        assertEquals(403, ex.getCode());
    }

    static class NonWorkerController {
        public void publicEndpoint() {
        }
    }

    static class WorkerController {
        @WorkerApi
        public void workerEndpoint() {
        }
    }
}
