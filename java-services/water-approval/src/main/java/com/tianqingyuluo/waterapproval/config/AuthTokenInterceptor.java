package com.tianqingyuluo.waterapproval.config;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.stp.StpUtil;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.controller.PublicApi;
import com.tianqingyuluo.waterapproval.controller.WorkerApi;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import java.lang.annotation.Annotation;

@Component
public class AuthTokenInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }

        if (hasAnnotation(handlerMethod, WorkerApi.class) || hasAnnotation(handlerMethod, PublicApi.class)) {
            return true;
        }

        try {
            StpUtil.checkLogin();
            return true;
        } catch (NotLoginException e) {
            throw new BusinessException(401, "未登录或登录已过期");
        }
    }

    private boolean hasAnnotation(HandlerMethod handlerMethod, Class<? extends Annotation> annotationClass) {
        if (handlerMethod.getMethodAnnotation(annotationClass) != null) {
            return true;
        }
        return handlerMethod.getBeanType().getAnnotation(annotationClass) != null;
    }
}
