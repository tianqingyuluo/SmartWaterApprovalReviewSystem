package com.tianqingyuluo.waterapproval.config;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.tianqingyuluo.waterapproval.common.RoleConstants;
import com.tianqingyuluo.waterapproval.entity.UserAccount;
import com.tianqingyuluo.waterapproval.mapper.UserAccountMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Slf4j
@Component
@RequiredArgsConstructor
public class UserSeedInitializer implements ApplicationRunner {

    private static final String DEFAULT_APPLICANT_USERNAME = "applicant";
    private static final String DEFAULT_APPLICANT_PASSWORD = "applicant123";

    private static final String DEFAULT_REVIEWER_USERNAME = "reviewer";
    private static final String DEFAULT_REVIEWER_PASSWORD = "reviewer123";

    private static final String DEFAULT_ADMIN_USERNAME = "admin";
    private static final String DEFAULT_ADMIN_PASSWORD = "admin123";

    private final UserAccountMapper userAccountMapper;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(ApplicationArguments args) {
        ensureUser(DEFAULT_APPLICANT_USERNAME, "默认申请人", RoleConstants.APPLICANT, DEFAULT_APPLICANT_PASSWORD);
        ensureUser(DEFAULT_REVIEWER_USERNAME, "默认审批员", RoleConstants.REVIEWER, DEFAULT_REVIEWER_PASSWORD);
        ensureUser(DEFAULT_ADMIN_USERNAME, "默认管理员", RoleConstants.ADMIN, DEFAULT_ADMIN_PASSWORD);
    }

    private void ensureUser(String username, String displayName, String roleCode, String rawPassword) {
        UserAccount existing = userAccountMapper.selectOne(
                new LambdaQueryWrapper<UserAccount>().eq(UserAccount::getUsername, username)
        );
        if (existing != null) {
            return;
        }

        UserAccount user = new UserAccount();
        user.setUsername(username);
        user.setDisplayName(displayName);
        user.setRoleCode(roleCode);
        user.setEnabled(1);
        user.setPasswordHash(passwordEncoder.encode(rawPassword));
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        userAccountMapper.insert(user);
        log.info("Initialized seed user: username={}, role={}", username, roleCode);
    }
}
