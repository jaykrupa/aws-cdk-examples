# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json
import logging
import uuid
from datetime import datetime

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_client = boto3.client("dynamodb")


def handler(event, context):
    # Task 4: Enhanced Lambda Function Security Logging
    # Log security-relevant request information
    request_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": context.aws_request_id,
        "source_ip": event.get("requestContext", {}).get("identity", {}).get("sourceIp"),
        "user_agent": event.get("requestContext", {}).get("identity", {}).get("userAgent"),
        "method": event.get("httpMethod"),
        "path": event.get("path"),
        "table_name": os.environ.get("TABLE_NAME"),
        "function_name": context.function_name,
        "function_version": context.function_version
    }
    
    logger.info(f"Security Event - API Request: {json.dumps(request_info)}")
    
    table = os.environ.get("TABLE_NAME")
    logger.info(f"## Loaded table name from environment variable TABLE_NAME: {table}")
    
    if event["body"]:
        item = json.loads(event["body"])
        logger.info(f"## Received payload: {item}")
        
        # Log data access events for write operations
        access_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "data_write",
            "table_name": table,
            "item_id": item.get("id"),
            "request_id": context.aws_request_id,
            "source_ip": event.get("requestContext", {}).get("identity", {}).get("sourceIp"),
            "operation": "put_item",
            "data_classification": "user_provided"
        }
        logger.info(f"Security Event - Data Access: {json.dumps(access_log)}")
        
        year = str(item["year"])
        title = str(item["title"])
        id = str(item["id"])
        
        try:
            dynamodb_client.put_item(
                TableName=table,
                Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
            )
            
            # Log successful data operation
            success_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "data_operation_success",
                "table_name": table,
                "item_id": id,
                "request_id": context.aws_request_id,
                "operation": "put_item"
            }
            logger.info(f"Security Event - Operation Success: {json.dumps(success_log)}")
            
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
        except Exception as e:
            # Log failed data operation
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "data_operation_failure",
                "table_name": table,
                "item_id": id,
                "request_id": context.aws_request_id,
                "operation": "put_item",
                "error": str(e)
            }
            logger.error(f"Security Event - Operation Failure: {json.dumps(error_log)}")
            raise
    else:
        logger.info("## Received request without a payload")
        
        # Generate UUID for default item
        default_id = str(uuid.uuid4())
        
        # Log data access events for default write operations
        access_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "data_write",
            "table_name": table,
            "item_id": default_id,
            "request_id": context.aws_request_id,
            "source_ip": event.get("requestContext", {}).get("identity", {}).get("sourceIp"),
            "operation": "put_item",
            "data_classification": "system_generated"
        }
        logger.info(f"Security Event - Data Access: {json.dumps(access_log)}")
        
        try:
            dynamodb_client.put_item(
                TableName=table,
                Item={
                    "year": {"N": "2012"},
                    "title": {"S": "The Amazing Spider-Man 2"},
                    "id": {"S": default_id},
                },
            )
            
            # Log successful data operation
            success_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "data_operation_success",
                "table_name": table,
                "item_id": default_id,
                "request_id": context.aws_request_id,
                "operation": "put_item"
            }
            logger.info(f"Security Event - Operation Success: {json.dumps(success_log)}")
            
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
        except Exception as e:
            # Log failed data operation
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "data_operation_failure",
                "table_name": table,
                "item_id": default_id,
                "request_id": context.aws_request_id,
                "operation": "put_item",
                "error": str(e)
            }
            logger.error(f"Security Event - Operation Failure: {json.dumps(error_log)}")
            raise
