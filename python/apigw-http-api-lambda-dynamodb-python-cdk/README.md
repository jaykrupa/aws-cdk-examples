
# AWS API Gateway HTTP API to AWS Lambda in VPC to DynamoDB CDK Python Sample!


## Overview

Creates an [AWS Lambda](https://aws.amazon.com/lambda/) function writing to [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and invoked by [Amazon API Gateway](https://aws.amazon.com/api-gateway/) REST API. 

This implementation includes **end-to-end X-Ray tracing** for compliance with AWS Well-Architected Framework **REL06-BP07: Monitor end-to-end tracing of requests through your system**.

![architecture](docs/architecture.png)

## Features

- **X-Ray Tracing**: Complete end-to-end tracing across API Gateway → Lambda → DynamoDB
- **CloudWatch Synthetics**: Automated API endpoint monitoring with synthetic transactions
- **VPC Isolation**: Lambda function deployed in private subnet with VPC endpoints
- **Error Handling**: Graceful degradation when X-Ray is unavailable
- **Monitoring**: Comprehensive observability with service maps and trace analysis

## X-Ray Tracing Components

1. **API Gateway Tracing**: Enabled at the deployment stage level
2. **Lambda Tracing**: Active tracing with X-Ray SDK instrumentation
3. **DynamoDB Tracing**: Automatic AWS SDK call instrumentation
4. **VPC Endpoint**: X-Ray interface endpoint for private subnet connectivity
5. **Synthetics Monitoring**: Canary tests running every 5 minutes

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

## Viewing X-Ray Traces

After making API requests, you can view the end-to-end traces in the AWS X-Ray console:

1. **Service Map**: Navigate to AWS X-Ray → Service map to see the complete request flow
2. **Traces**: View individual traces showing latency and errors across all components
3. **Analytics**: Use trace analytics to identify performance bottlenecks
4. **CloudWatch Synthetics**: Monitor the canary results in CloudWatch Synthetics console

### Expected Service Map Components:
- **API Gateway**: Entry point showing request volume and latency
- **Lambda Function**: Processing time and error rates
- **DynamoDB**: Database operation performance and throttling

## Monitoring and Alerting

The implementation includes:
- **CloudWatch Synthetics Canary**: Runs every 5 minutes to test API availability
- **X-Ray Service Map**: Visual representation of service dependencies
- **Trace Analytics**: Performance analysis and error detection
- **CloudWatch Metrics**: Standard Lambda and API Gateway metrics

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
