package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.common.R;
import com.tianqingyuluo.waterapproval.dto.LoginRequest;
import com.tianqingyuluo.waterapproval.dto.LoginResponse;
import com.tianqingyuluo.waterapproval.dto.UserProfileResponse;
import com.tianqingyuluo.waterapproval.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PublicApi
    @PostMapping("/login")
    public R<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        log.info("用户登录: username={}", request.getUsername());
        return R.ok(authService.login(request));
    }

    @GetMapping("/me")
    public R<UserProfileResponse> currentUser() {
        return R.ok(authService.currentUser());
    }
}
