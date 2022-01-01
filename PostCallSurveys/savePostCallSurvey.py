import boto3
from botocore.exceptions import ClientError
from datetime import datetime

def lambda_handler(event, context):


    print(event)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('PostCallSurveys')
    
    ContactId=event['Details']['ContactData']['ContactId']
    CLID=event['Details']['ContactData']['CustomerEndpoint']['Address']
    
    current_date =datetime.now()
    curren_date_string=current_date.strftime("%Y-%m-%d %H:%M:%S")
   
    
    answer=event['Details']['ContactData']['Attributes']['answer']
    
    try:
        response = table.put_item(
           Item={
                'ContactId':ContactId,
                'phoneNumber': CLID,
                'datetime': curren_date_string,
                'answer': answer
            }
        )
        
        return response

    
            
    except ClientError as e:
        print(e.response['Error']['Message'])
    
