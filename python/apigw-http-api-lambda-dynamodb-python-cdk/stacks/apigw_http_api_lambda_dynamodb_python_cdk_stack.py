# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb_,
    aws_lambda as lambda_,
    aws_apigateway as apigw_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_cloudtrail as cloudtrail,
    aws_s3 as s3,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
)
from constructs import Construct

TABLE_NAME = "demo_table"


class ApigwHttpApiLambdaDynamodbPythonCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            self,
            "Ingress",
            cidr="10.1.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private-Subnet", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
        )

        # Task 1: Configure AWS CloudTrail for API Activity Logging
        # Create S3 bucket for CloudTrail logs
        trail_bucket = s3.Bucket(
            self,
            "CloudTrailBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            auto_delete_objects=True  # For demo purposes
        )

        # Create CloudTrail
        trail = cloudtrail.Trail(
            self,
            "CloudTrail",
            bucket=trail_bucket,
            include_global_service_events=True,
            is_multi_region_trail=True,
            enable_file_validation=True
        )

        # Task 2: Enable VPC Flow Logs for Network Security Monitoring
        # Create IAM role for VPC Flow Logs
        flow_logs_role = iam.Role(
            self,
            "VpcFlowLogsRole",
            assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
            inline_policies={
                "FlowLogsDeliveryRolePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogGroups",
                                "logs:DescribeLogStreams"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Create CloudWatch Log Group for VPC Flow Logs with encryption
        flow_log_group = logs.LogGroup(
            self,
            "VpcFlowLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            # For demo purposes - enables easy cleanup and cost management in demo environments
            # In production environments, consider longer retention periods based on compliance requirements
            # and implement proper lifecycle policies for cost optimization
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            encryption_key=None  # Uses default CloudWatch Logs encryption
        )

        # Enable VPC Flow Logs
        vpc.add_flow_log(
            "FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                log_group=flow_log_group,
                iam_role=flow_logs_role
            )
        )
        
        # Create VPC endpoint
        dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
            self,
            "DynamoDBVpce",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            vpc=vpc,
        )

        # This allows to customize the endpoint policy
        dynamo_db_endpoint.add_to_policy(
            iam.PolicyStatement(  # Restrict to listing and describing tables
                principals=[iam.AnyPrincipal()],
                actions=[                "dynamodb:DescribeStream",
                "dynamodb:DescribeTable",
                "dynamodb:Get*",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:CreateTable",
                "dynamodb:Delete*",
                "dynamodb:Update*",
                "dynamodb:PutItem"],
                resources=["*"],
            )
        )

        # Create DynamoDb Table
        demo_table = dynamodb_.Table(
            self,
            TABLE_NAME,
            partition_key=dynamodb_.Attribute(
                name="id", type=dynamodb_.AttributeType.STRING
            ),
        )

        # Add data event selectors for comprehensive DynamoDB logging
        trail.add_event_selector(
            read_write_type=cloudtrail.ReadWriteType.ALL,
            include_management_events=True,
            data_resources=[
                cloudtrail.DataResource(
                    type="AWS::DynamoDB::Table",
                    values=[demo_table.table_arn]
                )
            ]
        )

        # Create the Lambda function to receive the request
        # First create explicit CloudWatch Log Group for Lambda
        # This change provides explicit control over Lambda logging configuration
        # instead of relying on AWS Lambda's automatic log group creation.
        # Benefits include: predefined retention policies, explicit IAM permissions,
        # consistent naming conventions, and better resource lifecycle management
        lambda_log_group = logs.LogGroup(
            self,
            "LambdaLogGroup",
            log_group_name=f"/aws/lambda/apigw_handler",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY  # For demo purposes
        )
        api_hanlder = lambda_.Function(
            self,
            "ApiHandler",
            function_name="apigw_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/apigw-handler"),
            handler="index.handler",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=1024,
            timeout=Duration.minutes(5),
        )

        # Ensure Lambda can write to its log group
        lambda_log_group.grant_write(api_hanlder)

        # grant permission to lambda to write to demo table
        demo_table.grant_write_data(api_hanlder)
        api_hanlder.add_environment("TABLE_NAME", demo_table.table_name)

        # Task 3: Configure API Gateway Access Logging
        # Create IAM role for API Gateway CloudWatch Logs
        api_gateway_logs_role = iam.Role(
            self,
            "ApiGatewayCloudWatchLogsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                )
            ]
        )

        # Create CloudWatch Log Group for API Gateway Access Logs
        api_log_group = logs.LogGroup(
            self,
            "ApiGatewayAccessLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY  # For demo purposes - enables easy cleanup in demo environments
        )

        # Configure API Gateway with access logging
        api_gateway = apigw_.LambdaRestApi(
            self,
            "Endpoint",
            handler=api_hanlder,
            deploy_options=apigw_.StageOptions(
                access_log_destination=apigw_.LogGroupLogDestination(api_log_group),
                access_log_format=apigw_.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                )
            )
        )

        # Set API Gateway account-level CloudWatch Logs role
        # Note: This is a one-time account-level setting for demo environments
        # In production, this would typically be configured once per AWS account
        apigw_.CfnAccount(
            self,
            "ApiGatewayAccount",
            cloud_watch_role_arn=api_gateway_logs_role.role_arn
        )
