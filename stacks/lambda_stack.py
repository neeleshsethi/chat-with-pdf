from aws_cdk import (
    
  
    Duration,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as iam,
    Fn as Fn
)


from constructs import Construct

class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, dict1, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create a Lambda layer
        layer = _lambda.LayerVersion(
            self, 'py-lib-layer',
            code=_lambda.Code.from_asset('assets/lambda_layer_with_py_deps.zip'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
        )

        agent_invokation_lambda = _lambda.Function(
            self, "AgentInvocationLambda",
            code=_lambda.Code.from_asset("lambda"),
            handler="agent_invocation.handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(60)
        )

        agent_invokation_lambda.add_layers(layer)

        CfnOutput(self, "AgentInvocationLambdaArn", value=agent_invokation_lambda.function_arn,
                  export_name = "AgentInvocationLambdaArn")
        
        self.agent_invokation_lambda_arn = agent_invokation_lambda.function_arn

        agent_invokation_lambda_ps = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        )

        agent_invokation_lambda.add_to_role_policy(agent_invokation_lambda_ps)





