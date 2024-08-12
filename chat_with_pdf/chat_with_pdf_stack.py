from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_opensearchserverless as opensearch,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
    App,

    


)
import aws_cdk as core


import random
import string
from constructs import Construct

class ChatWithPdfStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "ChatWithPdfQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        
        base_name = "chat-with-pdf-collection"  # Ensure base name is compliant with the pattern and length
        suffix_length = 32 - len(base_name) - 1  # Calculate the maximum length of the suffix

        if suffix_length < 1:
            raise ValueError("Base name is too long; suffix cannot be added.")

        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=suffix_length))
        collection_name = f"{base_name}-{unique_suffix}"

# Ensure the final name does not exceed 32 characters
        if len(collection_name) > 32:
            raise ValueError("Generated collection name exceeds the maximum length of 32 characters.")

        print(collection_name)  # For debugging purposes

        bucket_name = f"{base_name}-bucket-{unique_suffix}"
        pdf_bucket = s3.Bucket(
            self, 
            "PDFStorageBucket",
            bucket_name=bucket_name,
            versioned=True,  # Enable versioning for backups
            encryption=s3.BucketEncryption.S3_MANAGED,  # Enable server-side encryption
            removal_policy=core.RemovalPolicy.DESTROY  # Automatically clean up the bucket on stack deletion
        )


        # IAM Role for Bedrock Execution
        bedrock_execution_role = iam.Role(
            self, "BedrockExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Bedrock to access S3, OpenSearch, and other resources",
            role_name=f"AmazonBedrockExecutionRoleForKnowledgeBase_{unique_suffix}",
            max_session_duration=core.Duration.hours(1),
        )

        
        s3_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[pdf_bucket.bucket_arn, f"{pdf_bucket.bucket_arn}/*"],
            conditions={"StringEquals": {"aws:ResourceAccount": self.account}}
        )

     
        bedrock_execution_role.add_to_policy(s3_policy)


        
        opensearch_collection = opensearch.CfnCollection(self, "OpenSearchCollection",
            name=f"chat-with-pdf-collection",
           type="SEARCH"
        )

      
        opensearch_policy = iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[opensearch_collection.attr_arn]
        )
        bedrock_execution_role.add_to_policy(opensearch_policy)

      
        foundation_model_policy = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1",
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        )
        bedrock_execution_role.add_to_policy(foundation_model_policy)


        

        
        # Create OpenSearch Serverless access policy
        

        encryption_policy = opensearch.CfnSecurityPolicy(self, "EncryptionPolicy",
            name=f"bedrock-sample-rag-sp-{unique_suffix}",
            type="encryption",
            policy="{\"Rules\":[{\"Resource\":[\"collection/" + opensearch_collection.name + "\"],\"ResourceType\":\"collection\"}],\"AWSOwnedKey\":true}"
        )

        network_policy = opensearch.CfnSecurityPolicy(self, "NetworkPolicy",
            name=f"bedrock-sample-rag-np-{unique_suffix}",
            type="network",
            policy="[{\"Rules\":[{\"Resource\":[\"collection/" + opensearch_collection.name + "\"],\"ResourceType\":\"collection\"}],\"AllowFromPublic\":true}]"
        )

        access_policy = opensearch.CfnAccessPolicy(self, "AccessPolicy",
            name=f"bedrock-sample-rag-ap-{unique_suffix}",
            type="data",
            policy="[{\"Rules\":[{\"Resource\":[\"collection/" + opensearch_collection.name + "\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:DeleteCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DescribeCollectionItems\"],\"ResourceType\":\"collection\"},{\"Resource\":[\"index/" + opensearch_collection.name + "/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:DeleteIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"],\"ResourceType\":\"index\"}],\"Principal\":[\"" + self.account + "\",\"" + bedrock_execution_role.role_arn + "\"],\"Description\":\"Easy data policy\"}]"
        )



        

        # Output the bucket name and role ARN for reference
        core.CfnOutput(self, "BucketName", value=pdf_bucket.bucket_name)
        core.CfnOutput(self, "BedrockExecutionRoleArn", value=bedrock_execution_role.role_arn)
        core.CfnOutput(self, "OpenSearchCollectionArn", value=opensearch_collection.attr_arn)




       



