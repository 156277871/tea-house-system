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

# 上传最终完整包
print("正在上传最终完整部署包...")
with open("tea_house_lite/tea-house-complete.tar.gz", "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name="tea-house-complete.tar.gz",
        content_type="application/gzip",
    )
url = storage.generate_presigned_url(key=key, expire_time=604800)
print(f"✅ 最终完整部署包上传成功")
print(f"下载链接: {url}")
print()
print("=" * 60)
print("所有文件上传成功！")
print("=" * 60)
