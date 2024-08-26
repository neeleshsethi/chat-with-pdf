import boto3
from botocore.exceptions import ClientError
import os
import logging
import json


def handler(event, context):
    body = json.loads(event["body"])
    query = body['userPrompt']
    sessionId = body["sessionId"]
    boto3_session = boto3.Session()
    bedrock_agent_runtime_client = boto3_session.client('bedrock-agent-runtime', region_name=os.environ['AWS_REGION'])
    region_name = boto3_session.region_name
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0" 
    model_arn =  f'arn:aws:bedrock:{region_name}::foundation-model/{model_id}'

    print(f"Session: {sessionId} as question {query}")

    try:
        cfn_client = boto3.client('cloudformation')
    
        response = cfn_client.list_exports()
        
        for export in response['Exports']:
            if export['Name'] == 'BedrockKbId':
                kb_id = export['Value']
                break

            """
        
                            {
                        'citations': [
                            {
                                'generatedResponsePart': {
                                    'textResponsePart': {
                                        'span': {
                                            'end': 123,
                                            'start': 123
                                        },
                                        'text': 'string'
                                    }
                                },
                                'retrievedReferences': [
                                    {
                                        'content': {
                                            'text': 'string'
                                        },
                                        'location': {
                                            'confluenceLocation': {
                                                'url': 'string'
                                            },
                                            's3Location': {
                                                'uri': 'string'
                                            },
                                            'salesforceLocation': {
                                                'url': 'string'
                                            },
                                            'sharePointLocation': {
                                                'url': 'string'
                                            },
                                            'type': 'S3'|'WEB'|'CONFLUENCE'|'SALESFORCE'|'SHAREPOINT',
                                            'webLocation': {
                                                'url': 'string'
                                            }
                                        },
                                        'metadata': {
                                            'string': {...}|[...]|123|123.4|'string'|True|None
                                        }
                                    },
                                ]
                            },
                        ],
                        'guardrailAction': 'INTERVENED'|'NONE',
                        'output': {
                            'text': 'string'
                        },
                        'sessionId': 'string'
                    }
        """

        response = bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': model_arn
                    }
                },
            )
        generated_text = response['output']['text']
        sessionId = response['output']['sessionId']
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": generated_text,
                "sessionId": sessionId
            })
        }
    

    except ClientError as e:
        logging.error(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
      
  


