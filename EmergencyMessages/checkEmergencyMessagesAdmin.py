import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('EmergencyMessagesAdmin')
    
    PIN_Entered='unknown'
    PIN_DB='unknown'
    PIN_Entered=event['Details']['ContactData']['Attributes']['PIN']
    
    
  
    response = table.query(
            KeyConditionExpression=Key('PIN').eq(PIN_Entered)
       )
    resp=response['Items']
    
    try:    
        for item in resp:
            PIN_DB=item['PIN']
            
        
        if PIN_DB==PIN_Entered:
            resultMap = {"Valid":"1"}
        else:
            resultMap = {"Valid":"0"}
            
        return resultMap    
            
    except ClientError as e:
        print(e.response['Error']['Message'])
    