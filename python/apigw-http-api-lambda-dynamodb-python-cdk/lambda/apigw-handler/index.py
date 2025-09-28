# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize X-Ray SDK with error handling
try:
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    
    # Patch all AWS SDK calls
    patch_all()
    
    # Configure X-Ray recorder
    xray_recorder.configure(
        context_missing='LOG_ERROR',
        plugins=('EC2Plugin', 'ECSPlugin'),
        daemon_address=os.environ.get('_X_AMZN_TRACE_ID', '127.0.0.1:2000'),
        use_ssl=False
    )
    
    XRAY_AVAILABLE = True
    logger.info("X-Ray SDK initialized successfully")
except ImportError as e:
    logger.warning(f"X-Ray SDK not available: {e}")
    XRAY_AVAILABLE = False
    # Create a no-op decorator when X-Ray is not available
    def capture(name):
        def decorator(func):
            return func
        return decorator
    xray_recorder = type('MockXRayRecorder', (), {'capture': capture})()
except Exception as e:
    logger.error(f"Error initializing X-Ray SDK: {e}")
    XRAY_AVAILABLE = False
    def capture(name):
        def decorator(func):
            return func
        return decorator
    xray_recorder = type('MockXRayRecorder', (), {'capture': capture})()

dynamodb_client = boto3.client("dynamodb")


@xray_recorder.capture('lambda_handler')
def handler(event, context):
    table = os.environ.get("TABLE_NAME")
    logging.info(f"## Loaded table name from environemt variable DDB_TABLE: {table}")
    if event["body"]:
        item = json.loads(event["body"])
        logging.info(f"## Received payload: {item}")
        year = str(item["year"])
        title = str(item["title"])
        id = str(item["id"])
        dynamodb_client.put_item(
            TableName=table,
            Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
        )
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
    else:
        logging.info("## Received request without a payload")
        dynamodb_client.put_item(
            TableName=table,
            Item={
                "year": {"N": "2012"},
                "title": {"S": "The Amazing Spider-Man 2"},
                "id": {"S": str(uuid.uuid4())},
            },
        )
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
