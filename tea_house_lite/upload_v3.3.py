import os
from coze_coding_dev_sdk.s3 import S3SyncStorage

storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

with open("tea-house-essential-v3.3.tar.gz", "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name="tea-house-essential-v3.3.tar.gz",
        content_type="application/gzip",
    )
    print(f"上传成功! Key: {key}")

download_url = storage.generate_presigned_url(key=key, expire_time=3600)
print(f"下载链接: {download_url}")
