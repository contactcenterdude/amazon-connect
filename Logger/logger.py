import json
import boto3

def lambda_handler(event, context):
    
    print('### Event START ###')
    print(event)
    print('### Event END ###')
    
    resultMap = {"Status":"OK"}
    return resultMap
