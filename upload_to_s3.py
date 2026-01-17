import os
from coze_coding_dev_sdk.s3 import S3SyncStorage

# 初始化对象存储客户端
storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

# 上传文件
file_path = "tea_house_lite/tea-house-lite-complete.tar.gz"
with open(file_path, "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name="tea-house-lite-complete.tar.gz",
        content_type="application/gzip",
    )

# 生成签名URL（7天有效期）
signed_url = storage.generate_presigned_url(key=key, expire_time=604800)

print(f"上传成功！")
print(f"文件Key: {key}")
print(f"下载链接: {signed_url}")
