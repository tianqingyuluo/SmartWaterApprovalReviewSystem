package com.tianqingyuluo.waterapproval.service;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.LoginRequest;
import com.tianqingyuluo.waterapproval.dto.LoginResponse;
import com.tianqingyuluo.waterapproval.dto.UserProfileResponse;
import com.tianqingyuluo.waterapproval.entity.UserAccount;
import com.tianqingyuluo.waterapproval.mapper.UserAccountMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserAccountMapper userAccountMapper;
    private final PasswordEncoder passwordEncoder;

    @Override
    public LoginResponse login(LoginRequest request) {
        String username = request.getUsername().trim();
        UserAccount user = userAccountMapper.selectOne(
                new LambdaQueryWrapper<UserAccount>().eq(UserAccount::getUsername, username)
        );

        if (user == null || user.getEnabled() == null || user.getEnabled() != 1) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        StpUtil.login(user.getId());
        String token = StpUtil.getTokenValue();

        LoginResponse response = new LoginResponse();
        response.setToken(token);
        response.setUser(toProfile(user));
        return response;
    }

    @Override
    public UserProfileResponse currentUser() {
        Long userId = getCurrentLoginUserId();
        UserAccount user = userAccountMapper.selectOne(
                new LambdaQueryWrapper<UserAccount>()
                        .eq(UserAccount::getId, userId)
                        .eq(UserAccount::getEnabled, 1)
        );
        if (user == null) {
            throw new BusinessException(401, "登录已失效");
        }
        return toProfile(user);
    }

    private Long getCurrentLoginUserId() {
        try {
            StpUtil.checkLogin();
            return StpUtil.getLoginIdAsLong();
        } catch (NotLoginException e) {
            throw new BusinessException(401, "未登录或登录已过期");
        }
    }

    private UserProfileResponse toProfile(UserAccount user) {
        UserProfileResponse profile = new UserProfileResponse();
        profile.setUserId(user.getId());
        profile.setUsername(user.getUsername());
        profile.setDisplayName(user.getDisplayName());
        profile.setRole(user.getRoleCode());
        return profile;
    }
}
