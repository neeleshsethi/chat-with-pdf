from aws_cdk import (
    # Duration,
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_iam as iam,
    aws_bedrock as bedrock,
    aws_s3_deployment as s3d,
    aws_s3 as s3,
    aws_logs as logs,
    Fn as Fn,
    custom_resources as cr,
    

    


)
import hashlib
import uuid
import random
import string
from constructs import Construct





class BedrockStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, dict1, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        base_name = "chat-with-pdf-collection"
         # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8") 
        bucket_name = f"{base_name}-{hash_base_string}-bucket-{hash_base_string}"
        
         ### 1. Create S3 bucket for the Agent schema assets

        # Imporing and instantiating the access logs bucket so we can write the logs into it
        access_logs_bucket = s3.Bucket.from_bucket_name(self, "AccessLogsBucketName", Fn.import_value("AccessLogsBucketName"))
        
        
         # Create S3 bucket for the OpenAPI action group schemas 
        
        schema_bucket = s3.Bucket(self, "schema-bucket",
        bucket_name=("schema-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
        auto_delete_objects=True,
        versioned=True,
        removal_policy=RemovalPolicy.DESTROY,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        enforce_ssl=True,
        encryption=s3.BucketEncryption.S3_MANAGED,
        server_access_logs_bucket=access_logs_bucket,
        server_access_logs_prefix="schema-bucket-access-logs/",
        intelligent_tiering_configurations=[
            s3.IntelligentTieringConfiguration(
            name="my_s3_tiering",
            archive_access_tier_time=Duration.days(90),
            deep_archive_access_tier_time=Duration.days(180),
            prefix="prefix",
            tags=[s3.Tag(
                key="app",
                value="chat-with-pdf"
            )]
         )],      
        lifecycle_rules=[
            s3.LifecycleRule(
                noncurrent_version_expiration=Duration.days(7)
            )
        ],
    )
        


           # Create S3 bucket policy for bedrock permissions
        
        
        add_s3_policy = schema_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:*"],
                resources=[schema_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("bedrock.amazonaws.com")],
                )
            )
            
            
         # Upload schema from asset to S3 bucket
#        s3d.BucketDeployment(self, "DataDeployment",
#            sources=[s3d.Source.asset("assets/schema/")],
#           destination_bucket=schema_bucket,
#           destination_key_prefix="schema/"
#       )
        
            # Export the schema bucket name
        
        CfnOutput(self, "APISchemaBucket",
        value=schema_bucket.bucket_name,
        export_name="APISchemaBucket"
    )
        
        
        


            # Create a bedrock agent execution role (aka agent resource role) with permissions to interact with the services. The role name must follow a specific format.
        bedrock_agent_role = iam.Role(self, 'bedrock-agent-role',
            role_name=f'AmazonBedrockExecutionRoleForAgents_' + str(hashlib.sha384(hash_base_string).hexdigest())[:15],
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com'),
        )
        
        CfnOutput(self, "BedrockAgentRoleArn",
            value=bedrock_agent_role.role_arn,
            export_name="BedrockAgentRoleArn"
        )
        
        
        

        # Add model invocation inline permissions to the bedrock agent execution role
        bedrock_agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel", 
                    "bedrock:InvokeModelEndpoint", 
                    "bedrock:InvokeModelEndpointAsync"
                ],
                resources=[
                    "arn:aws:bedrock:{}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0".format(self.region),
                     f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1",
                     f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                ]
                ,
            )
        )
        
        bedrock_agent_role.add_to_policy(
            iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                    "s3:ListMultipartUploadParts",
                    "s3:AbortMultipartUpload",
                    "s3:CreateBucket",
                    "s3:PutObject",
                    "s3:PutBucketLogging",
                    "s3:PutBucketVersioning",
                    "s3:PutBucketNotification",
                ],
            resources=[
                    schema_bucket.bucket_arn,
                    f"{schema_bucket.bucket_arn}/*",
                    f"arn:aws:s3:::{Fn.import_value('DataSetBucketName')}",
                    f"arn:aws:s3:::{Fn.import_value('DataSetBucketName')}/*",
                    Fn.import_value('DataSetBucketArn'),
                    f"{Fn.import_value('DataSetBucketArn')}/*",
                    ],
            )
        ) 
        
         # Add knowledgebase opensearch serverless inline permissions to the bedrock agent execution role      
        bedrock_agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["aoss:APIAccessAll"],
                resources=["*"],
            )
        )
        
        
        
        
        
          # Create a S3 bucket for model invocation logs
        model_invocation_bucket = s3.Bucket(self, "model-invocation-bucket",
            bucket_name=("model-invocation-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            auto_delete_objects=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            server_access_logs_bucket=access_logs_bucket,
            server_access_logs_prefix="model-invocation-bucket-access-logs/",
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(14)
                )
            ],
        )
        
        # Create S3 bucket policy for bedrock permissions
        add_s3_policy = model_invocation_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject"
                ],
                resources=[model_invocation_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("bedrock.amazonaws.com")],
                )
            )
        
        # Create a Cloudwatch log group for model invocation logs
        model_log_group = logs.LogGroup(self, "model-log-group",
            log_group_name=("model-log-group-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            log_group_class=logs.LogGroupClass.STANDARD,
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create a dedicated role with permissions to write logs to cloudwatch logs.
        invocation_logging_role = iam.Role(self, 'invocation-logs-role',
            role_name=("InvocationLogsRole-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]).lower(),
            assumed_by=iam.ServicePrincipal('bedrock.amazonaws.com'),
        )

        # Add permission to log role to write logs to cloudwatch
        invocation_logging_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    model_log_group.log_group_arn,
                ]
                ,
            )
        )
        
        # Add permission to log role to write large log objects to S3
        invocation_logging_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "S3:PutObject"
                ],
                resources=[
                    model_invocation_bucket.bucket_arn,
                    model_invocation_bucket.bucket_arn + "/*"
                ]
                ,
            )
        )
        

      

      

     
        CfnOutput(self, "BedrockExecutionRoleArn", value=bedrock_agent_role.role_arn)

        








