package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

@Data
public class UserProfileResponse {
    private Long userId;
    private String username;
    private String displayName;
    private String role;
}
