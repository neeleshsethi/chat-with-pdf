from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_bedrock as bedrock,
    Fn as Fn,
    custom_resources as cr,
    aws_iam as iam,
)
from constructs import Construct
import hashlib


class KnowledgeBaseStack(Stack):

    def __init__(self, scope: Construct, id: str, dict1, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Create a unique string to create unique resource names
        hash_base_string = (self.account + self.region)
        hash_base_string = hash_base_string.encode("utf8")
        
       
        kb_bucket_name = Fn.import_value("KnowledgebaseBucketName")
        kb_bucket_arn = Fn.import_value("KnowledgebaseBucketArn")
        kb_role_arn = Fn.import_value("BedrockKbRoleArn")
        aoss_collection_arn = Fn.import_value("OpenSearchCollectionArn")        
        
        
        
         ### 1. Create bedrock knowledgebase for the agent
        
        index_name = "kb-docs"
        
        # Create the bedrock knowledgebase with the role arn that is referenced in the opensearch data access policy
        bedrock_knowledge_base = bedrock.CfnKnowledgeBase(self, "KnowledgeBaseDocs",
            name="bedrock-kb-docs",
            description="Bedrock knowledge base that contains a corpus of documents",
            role_arn=kb_role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{dict1['region']}::foundation-model/amazon.titan-embed-text-v1"
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=aoss_collection_arn,
                    vector_index_name=index_name,
                    field_mapping = bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        metadata_field="metadataField",
                        text_field="textField",
                        vector_field="vectorField"
                        )
                    ),
                ),
            tags={
                "owner": "saas"
                }
        )
        kb_id = bedrock_knowledge_base.ref


        CfnOutput(self, "BedrockKbName",
            value=bedrock_knowledge_base.name,
            export_name="BedrockKbName"
        )

        CfnOutput(self, "BedrockKbId",
            value=kb_id,
            export_name="BedrockKbId"
)
            
        
        
        kb_data_source = bedrock.CfnDataSource(self, "KbDataSource",
            name="KbDataSource",
            description="The S3 data source definition for the bedrock knowledge base",
            data_deletion_policy="RETAIN",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=kb_bucket_arn,
                    inclusion_prefixes=["eaa-docs"],
                ),
                type="S3"
            ),
            knowledge_base_id=bedrock_knowledge_base.ref,
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=300,
                        overlap_percentage=20
                    )
                )
            )
        )
        
        CfnOutput(self, "BedrockKbDataSourceName",
            value=kb_data_source.name,
            export_name="BedrockKbDataSourceName"
        ) 

        
        
        
        
        
