from aws_cdk import (
    
  
    Duration,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as iam,
    Fn as Fn,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
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
            code=_lambda.Code.from_asset("assets/lambda-bedrock"),
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
            actions=["bedrock:InvokeModel","cloudformation:ListExports",
                                "bedrock:Retrieve",
                                "bedrock:RetrieveAndGenerate"
                     
                     ],
            resources=["*"]
        )

        agent_invokation_lambda.add_to_role_policy(agent_invokation_lambda_ps)

        # Create VPC
        vpc = ec2.Vpc(self, "ChatbotVPC", max_azs=2)

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "ChatbotCluster", vpc=vpc)

        # Create Lambda function
    

        # Grant Lambda permission to invoke Bedrock
        agent_invokation_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
        self, "ChatbotService",
        cluster=cluster,
        cpu=512,
        memory_limit_mib=1024,
        desired_count=1,
        task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_asset("Admin"),
            container_port=80,
            environment={
                "LAMBDA_FUNCTION_NAME": agent_invokation_lambda.function_name,
            }
        ),
        health_check_grace_period=Duration.seconds(60),
    )

        fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Grant Fargate task permission to invoke Lambda
        agent_invokation_lambda.grant_invoke(fargate_service.task_definition.task_role)

       

  
        CfnOutput(self, "LoadBalancerDNS",
                  value=fargate_service.load_balancer.load_balancer_dns_name,
                  description="DNS name of the Application Load Balancer")
        

        streamlit_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
        self, "StreamlitService",
        cluster=cluster,
        cpu=512,
        memory_limit_mib=1024,
        desired_count=1,
        task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_asset("streamlit-app"),
            container_port=80,
            environment={
                "LAMBDA_FUNCTION_NAME": agent_invokation_lambda.function_name,
                "LOG_LEVEL": "INFO"
            }
        ),
        health_check_grace_period=Duration.seconds(60),
    )

        streamlit_fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Grant Fargate task permission to invoke Lambda
        agent_invokation_lambda.grant_invoke(streamlit_fargate_service.task_definition.task_role)

       

  
        CfnOutput(self, "StreamlitLoadBalancerDNS",
                  value=streamlit_fargate_service.load_balancer.load_balancer_dns_name,
                  description="DNS name of the Application Load Balancer")
        

