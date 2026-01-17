import os
from coze_coding_dev_sdk.s3 import S3SyncStorage

storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

file_path = "/workspace/projects/tea-house-github-files.tar.gz"

with open(file_path, "rb") as f:
    key = storage.stream_upload_file(
        fileobj=f,
        file_name="tea-house-github-files.tar.gz",
        content_type="application/gzip",
    )

download_url = storage.generate_presigned_url(key=key, expire_time=3600)
print(download_url)
