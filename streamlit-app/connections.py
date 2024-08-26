import os
import boto3
from botocore.config import Config

class Connections:
    session = boto3.session.Session()
    region_name = session.region_name or 'us-east-1'
    print(region_name)
    lambda_function_name = os.environ["LAMBDA_FUNCTION_NAME"]
    log_level = os.environ['LOG_LEVEL']

    lambda_client = boto3.client(
        "lambda",
        region_name=region_name,
        config=Config(read_timeout=300, connect_timeout=300),
    )
