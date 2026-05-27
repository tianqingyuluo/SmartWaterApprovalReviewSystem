package com.tianqingyuluo.waterapproval.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
public class MybatisPlusConfig implements WebMvcConfigurer {

    private final WorkerTokenInterceptor workerTokenInterceptor;
    private final AuthTokenInterceptor authTokenInterceptor;

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(workerTokenInterceptor).addPathPatterns("/task/**", "/material/**");
        registry.addInterceptor(authTokenInterceptor)
                .addPathPatterns("/task/**", "/ai/**", "/auth/**")
                .excludePathPatterns("/auth/login");
    }
}
