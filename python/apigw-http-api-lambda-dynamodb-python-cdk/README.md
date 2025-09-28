
# AWS API Gateway HTTP API to AWS Lambda in VPC to DynamoDB CDK Python Sample!


## Overview

Creates an [AWS Lambda](https://aws.amazon.com/lambda/) function writing to [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and invoked by [Amazon API Gateway](https://aws.amazon.com/api-gateway/) REST API with comprehensive security logging capabilities.

![architecture](docs/architecture.png)

## Security Logging Features

This implementation includes comprehensive security and application logging in compliance with AWS Well-Architected Framework SEC04-BP01:

### 1. AWS CloudTrail
- **Purpose**: Captures API-level security events and AWS service activity
- **Storage**: Secure S3 bucket with encryption and versioning
- **Features**: Multi-region trail with file validation enabled
- **Retention**: Configurable based on compliance requirements

### 2. VPC Flow Logs
- **Purpose**: Network-level security monitoring for Lambda function traffic
- **Destination**: CloudWatch Logs
- **Retention**: 1 month (configurable)
- **Coverage**: All VPC network interfaces

### 3. API Gateway Access Logging
- **Purpose**: Comprehensive API usage monitoring and security event tracking
- **Format**: Structured JSON with standard fields
- **Captured Data**: 
  - Caller information
  - HTTP method and path
  - Source IP address
  - Request/response timing
  - Status codes
  - User agent information

### 4. Lambda Function Security Logging
- **Purpose**: Structured security event logging for data access and operations
- **Event Types**:
  - API request events with security context
  - Data access events (read/write operations)
  - Operation success/failure events
  - Error and exception logging
- **Format**: Structured JSON for easy querying and analysis
- **Fields**: Timestamps, request IDs, source IPs, operation types, data classification

## Security Event Types Logged

1. **API Request Events**: Every incoming request with security context
2. **Data Access Events**: All DynamoDB operations with classification
3. **Operation Success/Failure**: Detailed outcome logging
4. **Network Flow Events**: VPC-level network traffic monitoring
5. **AWS Service Events**: CloudTrail captures all AWS API calls

## Log Analysis and Monitoring

All logs are structured for easy analysis using:
- **CloudWatch Logs Insights**: Query and analyze application logs
- **CloudTrail Event History**: Search and filter AWS API events
- **VPC Flow Logs**: Network traffic analysis and security monitoring

Example CloudWatch Logs Insights query for security events:
```
fields @timestamp, request_id, event_type, source_ip, operation
| filter event_type like /Security Event/
| sort @timestamp desc
| limit 100
```

## Setup

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Deploy
At this point you can deploy the stack. 

Using the default profile

```
$ cdk deploy
```

With specific profile

```
$ cdk deploy --profile test
```

## After Deploy
Navigate to AWS API Gateway console and test the API with below sample data 
```json
{
    "year":"2023", 
    "title":"kkkg",
    "id":"12"
}
```

You should get below response 

```json
{"message": "Successfully inserted data!"}
```

## Cleanup 
Run below script to delete AWS resources created by this sample stack.
```
cdk destroy
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
