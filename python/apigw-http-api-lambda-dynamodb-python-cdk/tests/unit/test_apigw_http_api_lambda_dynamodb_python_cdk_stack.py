import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.apigw_http_api_lambda_dynamodb_python_cdk_stack import ApigwHttpApiLambdaDynamodbPythonCdkStack


def test_security_logging_components_created():
    """Test that all security logging components are properly created"""
    app = core.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "apigw-http-api-lambda-dynamodb-python-cdk")
    template = assertions.Template.from_stack(stack)

    # Test CloudTrail S3 bucket is created with proper security settings
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {
            "ServerSideEncryptionConfiguration": [
                {
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        },
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        },
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })

    # Test CloudTrail is created with proper configuration
    template.has_resource_properties("AWS::CloudTrail::Trail", {
        "IncludeGlobalServiceEvents": True,
        "IsMultiRegionTrail": True,
        "EnableLogFileValidation": True
    })

    # Test VPC Flow Logs CloudWatch Log Group is created
    template.has_resource_properties("AWS::Logs::LogGroup", {
        "RetentionInDays": 30
    })

    # Test VPC Flow Logs are enabled
    template.has_resource_properties("AWS::EC2::FlowLog", {
        "ResourceType": "VPC",
        "TrafficType": "ALL"
    })

    # Test API Gateway has access logging configured
    template.has_resource_properties("AWS::ApiGateway::Stage", {
        "AccessLogSetting": {
            "Format": assertions.Match.string_like_regexp(r".*requestId.*sourceIp.*httpMethod.*")
        }
    })


def test_lambda_function_created():
    """Test that Lambda function is created with proper configuration"""
    app = core.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "apigw-http-api-lambda-dynamodb-python-cdk")
    template = assertions.Template.from_stack(stack)

    # Test Lambda function is created
    template.has_resource_properties("AWS::Lambda::Function", {
        "FunctionName": "apigw_handler",
        "Runtime": "python3.9",
        "Handler": "index.handler"
    })


def test_dynamodb_table_created():
    """Test that DynamoDB table is created"""
    app = core.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "apigw-http-api-lambda-dynamodb-python-cdk")
    template = assertions.Template.from_stack(stack)

    # Test DynamoDB table is created
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "KeySchema": [
            {
                "AttributeName": "id",
                "KeyType": "HASH"
            }
        ]
    })


def test_vpc_and_security_components():
    """Test VPC and security components are properly configured"""
    app = core.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "apigw-http-api-lambda-dynamodb-python-cdk")
    template = assertions.Template.from_stack(stack)

    # Test VPC is created
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.1.0.0/16"
    })

    # Test DynamoDB VPC Endpoint is created
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "ServiceName": assertions.Match.string_like_regexp(r".*dynamodb$")
    })


def test_iam_permissions():
    """Test that proper IAM permissions are configured"""
    app = core.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "apigw-http-api-lambda-dynamodb-python-cdk")
    template = assertions.Template.from_stack(stack)

    # Test Lambda execution role has DynamoDB permissions
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": assertions.Match.array_with(["dynamodb:PutItem"]),
                    "Effect": "Allow"
                })
            ])
        }
    })
