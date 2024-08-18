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
    aws_lambda as _lambda,
    custom_resources as cr,
    Duration,
    

    


)
import aws_cdk as core
import hashlib
import uuid
import random
import string
import json
from constructs import Construct

class AossStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, dict1, **kwargs) -> None:
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

        
       

        opensearch_serverless_collection = opensearchserverless.CfnCollection(self, "OpenSearchServerless",
            name="bedrock-kb",
            description="An opensearch serverless vector database for the bedrock knowledgebase",
            standby_replicas="DISABLED",
            type="VECTORSEARCH"
        )
        
        opensearch_serverless_collection.add_dependency(opensearch_serverless_network_policy)
        opensearch_serverless_collection.add_dependency(opensearch_serverless_encryption_policy)


        CfnOutput(self, "OpenSearchCollectionArn",
            value=opensearch_serverless_collection.attr_arn,
            export_name="OpenSearchCollectionArn"
        )

        CfnOutput(self, "OpenSearchCollectionEndpoint",
            value=opensearch_serverless_collection.attr_collection_endpoint,
            export_name="OpenSearchCollectionEndpoint"
        )
        
        
        # Create a bedrock knowledgebase role. Creating it here so we can reference it in the access policy for the opensearch serverless collection

        bedrock_kb_role = iam.Role(self, 'bedrock-kb-role',
            role_name=("bedrock-kb-role-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonBedrockFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonOpenSearchServiceFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'),
            ],
        )
        
        
        # Add inline permissions to the bedrock knowledgebase execution role      
        bedrock_kb_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "aoss:APIAccessAll",
                    "es:ESHttpPut", 
                    "iam:CreateServiceLinkedRole", 
                    "iam:PassRole", 
                    "iam:ListUsers",
                    "iam:ListRoles", 
                    ],
                resources=["*"],
            )
        )
        
        bedrock_kb_role_arn = bedrock_kb_role.role_arn
        
        CfnOutput(self, "BedrockKbRoleArn",
            value=bedrock_kb_role_arn,
            export_name="BedrockKbRoleArn"
        ) 


        # Define the Lambda function that creates a new index in the opensearch serverless collection

        create_index_lambda = _lambda.Function( self,"Index", 
                                                      runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("assets/lambda-index"),
            handler="create_oss_index.handler",
            timeout=core.Duration.seconds(60),
             environment={
                "COLLECTION_ENDPOINT": opensearch_serverless_collection.attr_collection_endpoint,
                "INDEX_NAME": index_name,
                "REGION": dict1['region'],
            }

        )
     # Define IAM permission policy for the Lambda function. This function calls the OpenSearch Serverless API to create a new index in the collection and must have the "aoss" permissions. 

        create_index_lambda.role.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "es:ESHttpPut", 
                "es:*", 
                "iam:CreateServiceLinkedRole", 
                "iam:PassRole", 
                "iam:ListUsers",
                "iam:ListRoles", 
                "aoss:APIAccessAll",
                "aoss:*"
            ],
            resources=["*"],
        ))   
        


                # Create a Lambda layer that contains the requests library, which we use to call the OpenSearch Serverless API


        layer = _lambda.LayerVersion( self,  'py-lib-layer-for-index',
                                     code=_lambda.Code.from_asset('assets/lambda_layer_with_py_deps.zip'),
                                     compatible_runtimes=[_lambda.Runtime.PYTHON_3_12])
        
        create_index_lambda.add_layers(layer)   

        
             # Finally we can create a complete data access policy for the collection that also includes the lambda function that will create the index. The policy must be a string and the resource contains the collections it is applied to.

        opensearch_serverless_access_policy = opensearchserverless.CfnAccessPolicy(self, "OpenSearchServerlessAccessPolicy",
            name=f"data-policy-" + str(uuid.uuid4())[-6:],
            policy=f"[{{\"Description\":\"Access for bedrock\",\"Rules\":[{{\"ResourceType\":\"index\",\"Resource\":[\"index/*/*\"],\"Permission\":[\"aoss:*\"]}},{{\"ResourceType\":\"collection\",\"Resource\":[\"collection/*\"],\"Permission\":[\"aoss:*\"]}}],\"Principal\":[\"{bedrock_role_arn}\",\"{bedrock_kb_role_arn}\"]}}]",
            type="data",
            description="the data access policy for the opensearch serverless collection"
        )
        
        opensearch_serverless_access_policy.add_dependency(opensearch_serverless_collection) 

        aossLambdaParams = {
                    "FunctionName": create_index_lambda.function_name,
                    "InvocationType": "RequestResponse"
                }
        
        # On creation of the stack, trigger the Lambda function we just defined 
        trigger_lambda_cr = cr.AwsCustomResource(self, "IndexCreateCustomResource",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters=aossLambdaParams,
                physical_resource_id=cr.PhysicalResourceId.of("Parameter.ARN")
                ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
                ),
            removal_policy = RemovalPolicy.DESTROY,
            timeout=Duration.seconds(120)
            )

        # Define IAM permission policy for the custom resource    
        trigger_lambda_cr.grant_principal.add_to_principal_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "lambda:*", 
                "iam:CreateServiceLinkedRole", 
                "iam:PassRole"
            ],
            resources=["*"],
            )
        )  
        
        # Only trigger the custom resource after the opensearch access policy has been applied to the collection    
        trigger_lambda_cr.node.add_dependency(opensearch_serverless_access_policy)
        trigger_lambda_cr.node.add_dependency(opensearch_serverless_collection)
        




        
        


    

        
                                
    






        

  




       



