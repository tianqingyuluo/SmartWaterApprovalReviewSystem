package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;
import org.springframework.web.multipart.MultipartFile;

@Data
public class SubmitRequest {
    private MultipartFile applicationForm;
    private MultipartFile businessLicense;
    private MultipartFile idCard;
}
