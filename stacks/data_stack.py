from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    Size,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3d,
    aws_glue as glue,
    aws_athena as athena,
    aws_kms as kms
)

from constructs import Construct
import hashlib

class DataFoundationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8")
         # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8")

        ### 0. Create access log bucket
        logs_bucket = s3.Bucket(self, "LogsBucket",
            bucket_name=("logs-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED
        )

        # Export the bucket name
        CfnOutput(self, "AccessLogsBucketName",
            value=logs_bucket.bucket_name,
            export_name="AccessLogsBucketName"
        )
        
        
         ### 1. Create data-set resources
        
        # Create S3 bucket for the data set
        data_bucket = s3.Bucket(self, "DataLake",
            bucket_name=("data-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            auto_delete_objects=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            server_access_logs_bucket=logs_bucket,
            server_access_logs_prefix="data-bucket-access-logs/",
            intelligent_tiering_configurations=[
                s3.IntelligentTieringConfiguration(
                name="my_s3_tiering",
                archive_access_tier_time=Duration.days(90),
                deep_archive_access_tier_time=Duration.days(180),
                prefix="prefix",
                tags=[s3.Tag(
                    key="key",
                    value="value"
                )]
             )],      
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(7)
                )
            ],
        )
        
        # Create S3 bucket policy for bedrock permissions
        add_s3_policy = data_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject","s3:PutObject","s3:AbortMultipartUpload"],
                resources=[data_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("bedrock.amazonaws.com")],
                )
            )
            
            
        
        # Export the data set bucket name
        CfnOutput(self, "DataSetBucketName",
            value=data_bucket.bucket_name,
            export_name="DataSetBucketName"
        )
        
        CfnOutput(self, "DataSetBucketArn",
            value=data_bucket.bucket_arn,
            export_name="DataSetBucketArn"
        )
        
        
         ### 4. Create knowledgebase bucket and upload corpus of documents
        
        # Create S3 bucket for the knowledgebase assets
        kb_bucket = s3.Bucket(self, "Knowledgebase",
            bucket_name=("knowledgebase-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            auto_delete_objects=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            server_access_logs_bucket=logs_bucket,
            server_access_logs_prefix="knowledgebase-access-logs/",
            intelligent_tiering_configurations=[
                s3.IntelligentTieringConfiguration(
                name="my_s3_tiering",
                archive_access_tier_time=Duration.days(90),
                deep_archive_access_tier_time=Duration.days(180),
                prefix="prefix",
                tags=[s3.Tag(
                    key="key",
                    value="value"
                )]
             )],      
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(7)
                )
            ],
        )

        kb_bucket.grant_read_write(iam.ServicePrincipal("bedrock.amazonaws.com"))
        
        # Export the kb bucket bucket name
        CfnOutput(self, "KnowledgebaseBucketName",
            value=kb_bucket.bucket_name,
            export_name="KnowledgebaseBucketName"
        )
        
        # Export the kb bucket bucket arn
        CfnOutput(self, "KnowledgebaseBucketArn",
            value=kb_bucket.bucket_arn,
            export_name="KnowledgebaseBucketArn"
        )

        
        
        