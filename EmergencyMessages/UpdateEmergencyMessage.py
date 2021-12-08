import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('EmergencyMessages')
    
    MessageID=event['Details']['ContactData']['Attributes']['MessageID']
    Status=event['Details']['ContactData']['Attributes']['Status']
    
    print("MessageID: "+MessageID)
    print("current status: " + Status)
    
    if Status=="true":
        NewStatus="false"
        
    if Status=="false":
        NewStatus="true"
    
    print("new status: "+NewStatus)
    response = table.update_item(
        Key={
            'id': MessageID,
        },
        UpdateExpression="set Enabled=:r",
        ExpressionAttributeValues={
            ':r': NewStatus
        }
    )

    print("UpdateItem succeeded")
    
    resultMap = {"OK":"1"}
    return resultMap