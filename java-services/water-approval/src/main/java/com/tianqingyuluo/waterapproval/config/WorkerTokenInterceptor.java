package com.tianqingyuluo.waterapproval.config;

import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.controller.WorkerApi;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

@Slf4j
@Component
public class WorkerTokenInterceptor implements HandlerInterceptor {

    @Value("${water-approval.worker.token:}")
    private String workerToken;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }

        WorkerApi annotation = handlerMethod.getMethodAnnotation(WorkerApi.class);
        if (annotation == null) {
            annotation = handlerMethod.getBeanType().getAnnotation(WorkerApi.class);
        }

        if (annotation == null) {
            return true;
        }

        if (workerToken == null || workerToken.isEmpty()) {
            log.warn("Worker token not configured, blocking Worker API access");
            throw new BusinessException(403, "Worker API access denied: token not configured");
        }

        String token = request.getHeader("X-Worker-Token");
        if (!workerToken.equals(token)) {
            log.warn("Invalid worker token for {} {}", request.getMethod(), request.getRequestURI());
            throw new BusinessException(403, "Invalid worker token");
        }

        return true;
    }
}
