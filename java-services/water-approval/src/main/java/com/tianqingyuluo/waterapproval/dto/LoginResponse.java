package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private UserProfileResponse user;
}
