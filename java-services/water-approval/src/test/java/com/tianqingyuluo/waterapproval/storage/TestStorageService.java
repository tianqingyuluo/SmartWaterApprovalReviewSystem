package com.tianqingyuluo.waterapproval.storage;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
@Profile("test")
public class TestStorageService implements StorageService {

    private final Map<String, byte[]> store = new ConcurrentHashMap<>();

    @Override
    public String upload(String key, InputStream inputStream, long size, String contentType) {
        try {
            byte[] data = inputStream.readAllBytes();
            store.put(key, data);
            return key;
        } catch (Exception e) {
            throw new RuntimeException("Test storage upload failed", e);
        }
    }

    @Override
    public InputStream download(String key) {
        byte[] data = store.get(key);
        if (data == null) {
            throw new RuntimeException("File not found in test storage: " + key);
        }
        return new ByteArrayInputStream(data);
    }

    @Override
    public void delete(String key) {
        store.remove(key);
    }

    @Override
    public String getUrl(String key) {
        return "test://storage/" + key;
    }
}
