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

        # Create Fargate Service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "ChatbotService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("Admin"),
                container_port=8501,
                environment={
                    "LAMBDA_FUNCTION_NAME": agent_invokation_lambda.function_name,
                }
            ),
        )

        # Grant Fargate task permission to invoke Lambda
        agent_invokation_lambda.grant_invoke(fargate_service.task_definition.task_role)

         # Create EC2 Instance
        ec2_instance = ec2.Instance(
            self, "TestInstance",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        # Allow EC2 instance to access the Fargate service
        fargate_service.load_balancer.connections.allow_from(
            ec2_instance, ec2.Port.tcp(80), "Allow EC2 instance to access ALB"
        )

        # Output the EC2 instance public IP and the ALB DNS name
        CfnOutput(self, "EC2InstancePublicIP",
                  value=ec2_instance.instance_public_ip,
                  description="Public IP address of the EC2 instance")
        CfnOutput(self, "LoadBalancerDNS",
                  value=fargate_service.load_balancer.load_balancer_dns_name,
                  description="DNS name of the Application Load Balancer")
        

