package com.tianqingyuluo.waterapproval.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.io.InputStream;

@Data
@AllArgsConstructor
public class MaterialPreviewResource {
    private InputStream inputStream;
    private String contentType;
    private String originalFileName;
    private Long fileSize;
    private String fileExtension;
}
