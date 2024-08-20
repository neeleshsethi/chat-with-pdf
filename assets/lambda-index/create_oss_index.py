#from requests import request
import json
import os
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from time import sleep
from retrying import retry
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

boto3_session = boto3.Session()
region_name = boto3_session.region_name
sts_client = boto3.client('sts')
account_id = sts_client.get_caller_identity()["Account"]
credentials = boto3_session.get_credentials()
# opensearch service
service = 'aoss'
awsauth = auth = AWSV4SignerAuth(credentials, region_name, service)


def handler(event, context):
    # 1. Defining the request body for the index and field creation
    host = os.environ["COLLECTION_ENDPOINT"].replace("https://", "")

    print(f"Collection Endpoint: " + host)
    index_name = os.environ["INDEX_NAME"]
    print(f"Index name: " + index_name)


    body_json = {
                "settings": {
                    "index.knn": "true"
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "innerproduct",
                                "engine": "faiss",
                                "parameters": {
                                "ef_construction": 256,
                                "m": 48
                                }
                            }
                        },
                        "text": {
                            "type": "text"
                        },
                        "text-metadata": {
                            "type": "text"         
                        }
                    }
                }
                }
  
  

    try:        
        
            oss_client = OpenSearch(
                        hosts=[{'host': host, 'port': 443}],
                        http_auth=awsauth,
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection,
                        timeout=30
                    )
       
            response = oss_client.indices.create(index=index_name, body=json.dumps(body_json))
            print('\nCreating index:')
            print(response)
            return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Index created successfully',
                'index_name': index_name,
                'response': response
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }


    except Exception as e:
            print(f"Error trying to create aoss index...{e}")
            return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error creating index',
                'error': e
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
