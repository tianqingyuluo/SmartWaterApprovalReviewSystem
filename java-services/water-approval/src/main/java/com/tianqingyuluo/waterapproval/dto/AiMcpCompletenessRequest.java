package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class AiMcpCompletenessRequest {
    private List<String> materials = new ArrayList<>();
}
