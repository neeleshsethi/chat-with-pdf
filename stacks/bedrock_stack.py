from aws_cdk import (
    # Duration,
    Stack,
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





class BedrockStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        base_name = "chat-with-pdf-collection"
         # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8") 
        bucket_name = f"{base_name}-{hash_base_string}-bucket-{hash_base_string}"


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
            role_name=f"AmazonBedrockExecutionRoleForKnowledgeBase_{hash_base_string}_{hash_base_string}",
            max_session_duration=core.Duration.hours(1),
        )


        s3_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[pdf_bucket.bucket_arn, f"{pdf_bucket.bucket_arn}/*"],
            conditions={"StringEquals": {"aws:ResourceAccount": self.account}}
        )


        bedrock_execution_role.add_to_policy(s3_policy)

        foundation_model_policy = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1",
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        )
        bedrock_execution_role.add_to_policy(foundation_model_policy)

        core.CfnOutput(self, "BucketName", value=pdf_bucket.bucket_name)
        core.CfnOutput(self, "BedrockExecutionRoleArn", value=bedrock_execution_role.role_arn)

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
                actions=["aoss:APIAccessAll"],
                resources=["*"],
            )
        )
        
        bedrock_kb_role_arn = bedrock_kb_role.role_arn
        bedrock_role_arn = bedrock_execution_role.role_arn











