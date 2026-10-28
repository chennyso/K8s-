import json
from pathlib import Path

import boto3
from botocore.config import Config

values = json.loads(Path("private/s3-client.json").read_text())
client = boto3.client("s3", endpoint_url=values["endpoint"], aws_access_key_id=values["access"], aws_secret_access_key=values["secret"], region_name="us-east-1", config=Config(proxies={}, s3={"addressing_style": "path"}))
client.create_bucket(Bucket="bbt-juicefs")
client.put_object(Bucket="bbt-juicefs", Key="installation-check.txt", Body=b"BBT storage installation check\n")
value = client.get_object(Bucket="bbt-juicefs", Key="installation-check.txt")["Body"].read()
if value != b"BBT storage installation check\n":
    raise ValueError("S3 读取结果与实际写入内容不一致")
print("S3 创建、写入和读取验证通过")
