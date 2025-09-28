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
    aws_synthetics as synthetics,
    BundlingOptions,
    Duration,
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
        
        # Create VPC endpoint
        dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
            self,
            "DynamoDBVpce",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            vpc=vpc,
        )

        # Create VPC endpoint for X-Ray to allow Lambda in private subnet to send traces
        xray_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "XRayVpce",
            service=ec2.InterfaceVpcEndpointAwsService.XRAY,
            vpc=vpc,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            )
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

        # Create the Lambda function to receive the request
        api_hanlder = lambda_.Function(
            self,
            "ApiHandler",
            function_name="apigw_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(
                "lambda/apigw-handler",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            handler="index.handler",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=1024,
            timeout=Duration.minutes(5),
            tracing=lambda_.Tracing.ACTIVE,
        )

        # grant permission to lambda to write to demo table
        demo_table.grant_write_data(api_hanlder)
        api_hanlder.add_environment("TABLE_NAME", demo_table.table_name)
        
        # Add X-Ray configuration environment variables
        api_hanlder.add_environment("_X_AMZN_TRACE_ID", "Root=1-00000000-000000000000000000000000")
        api_hanlder.add_environment("AWS_XRAY_CONTEXT_MISSING", "LOG_ERROR")
        api_hanlder.add_environment("AWS_XRAY_TRACING_NAME", "apigw-lambda-dynamodb")

        # Grant X-Ray tracing permissions to Lambda
        api_hanlder.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

        # Create API Gateway
        api_gateway = apigw_.LambdaRestApi(
            self,
            "Endpoint",
            handler=api_hanlder,
            deploy_options=apigw_.StageOptions(
                tracing_enabled=True
            )
        )

        # Create CloudWatch Synthetics Canary for API monitoring
        canary = synthetics.Canary(
            self,
            "ApiCanary",
            canary_name="api-endpoint-canary",
            test=synthetics.Test.custom(
                code=synthetics.Code.from_inline("""
const synthetics = require('Synthetics');

const apiCanaryBlueprint = async function () {
    const postData = JSON.stringify({
        "year": "2023",
        "title": "Test Movie",
        "id": "test-id"
    });
    
    return await synthetics.executeStep('checkApiEndpoint', async function () {
        return await synthetics.makeRequest({
            hostname: process.env.API_HOSTNAME,
            method: 'POST',
            path: '/prod/',
            headers: {
                'Content-Type': 'application/json'
            },
            body: postData
        });
    });
};

exports.handler = async () => {
    return await synthetics.executeStep('apiCanaryBlueprint', apiCanaryBlueprint);
};
                """),
                handler="index.handler"
            ),
            runtime=synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_9,
            schedule=synthetics.Schedule.rate(Duration.minutes(5)),
            environment_variables={
                "API_HOSTNAME": f"{api_gateway.rest_api_id}.execute-api.{self.region}.amazonaws.com"
            }
        )
