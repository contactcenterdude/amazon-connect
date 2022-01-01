import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Clients')
    
    message="Link on how to setup our new mobile application http://tinyurl.com/AmazonConnectSMS"
    
    CLID=event['Details']['ContactData']['CustomerEndpoint']['Address']

    response = table.query(
            KeyConditionExpression=Key('phoneNumber').eq(CLID)
        )
    resp=response['Items']
    
    for item in resp:
            phoneNumber=item['phoneNumber']

            if phoneNumber==CLID:            
                 # Create an SNS client
                client = boto3.client("sns",region_name="us-east-1")
            
        
                # Send SMS message
                client.publish(
                    PhoneNumber=CLID,
                    Message=message
                )
    
                return {
                    'statusCode': 200,
                    'body': json.dumps('OK')
                }
