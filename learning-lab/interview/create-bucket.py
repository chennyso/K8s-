import json
import pathlib

import boto3
from botocore.config import Config

root = pathlib.Path(__file__).resolve().parent
values = json.loads((root / "secrets/platform.json").read_text())
client = boto3.client("s3", endpoint_url="http://127.0.0.1:18333", aws_access_key_id=values["s3key"], aws_secret_access_key=values["s3secret"], region_name="us-east-1", config=Config(proxies={}, s3={"addressing_style": "path"}))
client.create_bucket(Bucket="velero")
client.put_object(Bucket="velero", Key="acceptance.txt", Body=b"204 real object storage acceptance")
body = client.get_object(Bucket="velero", Key="acceptance.txt")["Body"].read()
assert body == b"204 real object storage acceptance"
print("S3 创建存储桶、写入与读取校验通过")
