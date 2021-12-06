import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('EmergencyMessages')
    
    Enabled='unknown'
    Text=''
    Action=''
    ActionTarget=''
    
    MessageID=event['Details']['ContactData']['Attributes']['MessageID']
    
    

  
    response = table.query(
            KeyConditionExpression=Key('id').eq(MessageID)
       )
    resp=response['Items']
    
    try:    
        for item in resp:
            Enabled=item['Enabled']
            Text=item['Text']
            Action=item['Action']
            ActionTarget=item['ActionTarget']
            
        resultMap = {"Enabled":Enabled,"Text":Text,"Action":Action,"ActionTarget":ActionTarget}
        return resultMap    
            
    except ClientError as e:
        print(e.response['Error']['Message'])
    