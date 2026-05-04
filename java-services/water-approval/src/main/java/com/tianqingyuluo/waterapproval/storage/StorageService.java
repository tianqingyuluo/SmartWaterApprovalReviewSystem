package com.tianqingyuluo.waterapproval.storage;

import java.io.InputStream;

public interface StorageService {
    String upload(String key, InputStream inputStream, long size, String contentType);
    InputStream download(String key);
    void delete(String key);
    String getUrl(String key);
}
