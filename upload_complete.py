import os
from coze_coding_dev_sdk.s3 import S3SyncStorage

# 初始化对象存储
storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

# 上传文件
file_path = "/workspace/projects/tea-house-complete.tar.gz"
file_name = "tea-house-complete.tar.gz"

print(f"正在上传文件: {file_path}")

with open(file_path, "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name=file_name,
        content_type="application/gzip",
    )

print(f"上传成功，文件key: {key}")

# 生成下载链接
download_url = storage.generate_presigned_url(key=key, expire_time=3600)
print(f"\n下载链接（1小时有效）:\n{download_url}")
