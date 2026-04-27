package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.service.ReviewTaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.InputStream;

@Slf4j
@RestController
@RequestMapping("/material")
public class MaterialController {

    @Autowired
    private ReviewTaskService reviewTaskService;

    @GetMapping("/download")
    public ResponseEntity<InputStreamResource> download(@RequestParam String key) {
        log.info("下载材料: key={}", key);
        InputStream inputStream = reviewTaskService.downloadMaterial(key);
        String contentType = reviewTaskService.getMaterialContentType(key);

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(
                        contentType != null ? contentType : "application/octet-stream"
                ))
                .body(new InputStreamResource(inputStream));
    }
}
