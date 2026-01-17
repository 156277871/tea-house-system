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

# 上传 V2.0 完整包
print("正在上传茶楼管理系统 V2.0...")
with open("tea_house_lite/tea-house-v2-complete.tar.gz", "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name="tea-house-v2-complete.tar.gz",
        content_type="application/gzip",
    )
url = storage.generate_presigned_url(key=key, expire_time=604800)
print(f"✅ V2.0 上传成功")
print(f"下载链接: {url}")
print()
print("=" * 60)
print("V2.0 上传成功！包含开台、点单、结账功能")
print("=" * 60)
