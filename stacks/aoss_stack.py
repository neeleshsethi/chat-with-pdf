from aws_cdk import (
    # Duration,
    Stack,
    Fn,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_opensearchserverless as opensearchserverless,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
    App,
    Aws,
    
    

    


)
import aws_cdk as core
import hashlib
import uuid
import random
import string
from constructs import Construct

class AossStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        index_name = "kb-docs"

    
         # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8")   
        
      
        opensearch_serverless_encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "OpenSearchServerlessEncryptionPolicy",
            name="encryption-policy",
            policy="{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/*\"]}],\"AWSOwnedKey\":true}",
            type="encryption",
            description="the encryption policy for the opensearch serverless collection"
        )
        
        opensearch_serverless_network_policy = opensearchserverless.CfnSecurityPolicy(self, "OpenSearchServerlessNetworkPolicy",
            name="network-policy",
            policy="[{\"Description\":\"Public access for collection\",\"Rules\":[{\"ResourceType\":\"dashboard\",\"Resource\":[\"collection/*\"]},{\"ResourceType\":\"collection\",\"Resource\":[\"collection/*\"]}],\"AllowFromPublic\":true}]",
            type="network",
            description="the network policy for the opensearch serverless collection"
        )

        bedrock_role_arn = Fn.import_value("BedrockAgentRoleArn")
        bedrock_kb_role_arn = Fn.import_value("bedrock_kb_role_arn")

        
        opensearch_serverless_access_policy = opensearchserverless.CfnAccessPolicy(self, "OpenSearchServerlessAccessPolicy",
            name=f"data-policy-" + str(uuid.uuid4())[-6:],
            policy=f"[{{\"Description\":\"Access for bedrock\",\"Rules\":[{{\"ResourceType\":\"index\",\"Resource\":[\"index/*/*\"],\"Permission\":[\"aoss:*\"]}},{{\"ResourceType\":\"collection\",\"Resource\":[\"collection/*\"],\"Permission\":[\"aoss:*\"]}}],\"Principal\":[\"{bedrock_role_arn}\",\"{bedrock_kb_role_arn}\"]}}]",
            type="data",
            description="the data access policy for the opensearch serverless collection"
        )


        opensearch_serverless_collection = opensearchserverless.CfnCollection(self, "OpenSearchServerless",
            name="bedrock-kb",
            description="An opensearch serverless vector database for the bedrock knowledgebase",
            standby_replicas="DISABLED",
            type="VECTORSEARCH"
        )
        
        opensearch_serverless_collection.add_dependency(opensearch_serverless_network_policy)
        opensearch_serverless_collection.add_dependency(opensearch_serverless_access_policy)
      
        CfnOutput(self, "OpenSearchCollectionArn",
            value=opensearch_serverless_collection.attr_arn,
            export_name="OpenSearchCollectionArn"
        )

        CfnOutput(self, "OpenSearchCollectionEndpoint",
            value=opensearch_serverless_collection.attr_collection_endpoint,
            export_name="OpenSearchCollectionEndpoint"
        )


        

  




       



