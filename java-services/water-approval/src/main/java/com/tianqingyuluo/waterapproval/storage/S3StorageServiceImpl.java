package com.tianqingyuluo.waterapproval.storage;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;

import jakarta.annotation.PostConstruct;
import java.io.InputStream;
import java.net.URI;

@Slf4j
@Service
@RequiredArgsConstructor
@Profile("!test")
public class S3StorageServiceImpl implements StorageService {

    private final StorageProperties properties;

    private S3Client s3Client;
    private boolean initialized = false;

    @PostConstruct
    public void init() {
        String accessKey = properties.getAccessKey();
        String secretKey = properties.getSecretKey();

        if (accessKey == null || accessKey.isBlank() || secretKey == null || secretKey.isBlank()) {
            log.warn("S3 credentials not configured; S3StorageService will operate in degraded mode");
            return;
        }

        AwsBasicCredentials credentials = AwsBasicCredentials.create(accessKey, secretKey);

        s3Client = S3Client.builder()
                .endpointOverride(URI.create(properties.getEndpoint()))
                .region(Region.of(properties.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .forcePathStyle(true)
                .build();

        initialized = true;
        createBucketIfNotExists();
    }

    private void createBucketIfNotExists() {
        try {
            HeadBucketRequest headBucketRequest = HeadBucketRequest.builder()
                    .bucket(properties.getBucketName())
                    .build();
            s3Client.headBucket(headBucketRequest);
        } catch (NoSuchBucketException e) {
            CreateBucketRequest createBucketRequest = CreateBucketRequest.builder()
                    .bucket(properties.getBucketName())
                    .build();
            s3Client.createBucket(createBucketRequest);
            log.info("Created bucket: {}", properties.getBucketName());
        }
    }

    @Override
    public String upload(String key, InputStream inputStream, long size, String contentType) {
        if (!initialized) {
            throw new IllegalStateException("S3 storage is not initialized");
        }
        PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .bucket(properties.getBucketName())
                .key(key)
                .contentType(contentType)
                .contentLength(size)
                .build();

        s3Client.putObject(putObjectRequest, RequestBody.fromInputStream(inputStream, size));
        log.info("Uploaded file: {}", key);
        return key;
    }

    @Override
    public InputStream download(String key) {
        if (!initialized) {
            throw new IllegalStateException("S3 storage is not initialized");
        }
        GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                .bucket(properties.getBucketName())
                .key(key)
                .build();

        return s3Client.getObject(getObjectRequest);
    }

    @Override
    public void delete(String key) {
        if (!initialized) {
            throw new IllegalStateException("S3 storage is not initialized");
        }
        DeleteObjectRequest deleteObjectRequest = DeleteObjectRequest.builder()
                .bucket(properties.getBucketName())
                .key(key)
                .build();

        s3Client.deleteObject(deleteObjectRequest);
        log.info("Deleted file: {}", key);
    }

    @Override
    public String getUrl(String key) {
        return properties.getEndpoint() + "/" + properties.getBucketName() + "/" + key;
    }
}
