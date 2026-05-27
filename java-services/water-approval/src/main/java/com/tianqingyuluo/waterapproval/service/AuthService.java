package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.LoginRequest;
import com.tianqingyuluo.waterapproval.dto.LoginResponse;
import com.tianqingyuluo.waterapproval.dto.UserProfileResponse;

public interface AuthService {
    LoginResponse login(LoginRequest request);

    UserProfileResponse currentUser();
}
