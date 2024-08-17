#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.aoss_stack import AossStack
from stacks.bedrock_stack import BedrockStack
from stacks.data_stack import DataFoundationStack
from stacks.kb_stack import KnowledgeBaseStack
from stacks.lambda_stack import LambdaStack


app = cdk.App()


dict1 = {
    "region": 'us-east-1',
    "account_id": '117134819170'
}



stack1 = DataFoundationStack(app, "DataStack",
            env=cdk.Environment(account=dict1['account_id'], region=dict1['region']),
            description="Data foundations for the bedrock agent", 
            termination_protection=False, 
            tags={"project":"bedrock-agents"},
)

stack3 = BedrockStack(app, "BedrockAgentStack",
            env=cdk.Environment(account=dict1['account_id'], region=dict1['region']),
            description="Bedrock agent resources", 
            termination_protection=False, 
            tags={"project":"bedrock-agents"},
            dict1=dict1,
         
)

stack4 = AossStack(app, "AossStack",
            env=cdk.Environment(account=dict1['account_id'], region=dict1['region']),
            description="Opensearch Serverless resources", 
            termination_protection=False, 
            tags={"project":"bedrock-agents"},
            dict1=dict1,
         
)


stack5 = KnowledgeBaseStack(app, "KnowledgebaseStack",
            env=cdk.Environment(account=dict1['account_id'], region=dict1['region']),
            description="Bedrock knowledgebase resources", 
            termination_protection=False, 
            tags={"project":"bedrock-agents"},
            dict1=dict1,
           
)

stack6 = LambdaStack(app, "LambdaStack",
            env=cdk.Environment(account=dict1['account_id'], region=dict1['region']),
            description="Lambda resources", 
            termination_protection=False, 
            tags={"project":"bedrock-agents"},
            dict1=dict1,
           
)


stack3.add_dependency(stack1)

stack4.add_dependency(stack3)
stack5.add_dependency(stack4)
stack6.add_dependency(stack5)
cdk.Tags.of(stack1).add(key="owner",value="acs")

cdk.Tags.of(stack3).add(key="owner",value="acs")
cdk.Tags.of(stack4).add(key="owner",value="acs")
cdk.Tags.of(stack5).add(key="owner",value="acs")


app.synth()
