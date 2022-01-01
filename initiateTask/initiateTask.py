import json
import boto3


def lambda_handler(event, context):
    
    accountNumber=event['Details']['ContactData']['Attributes']['accountNumber']
    requestType=event['Details']['ContactData']['Attributes']['requestType']
    CLID=event['Details']['ContactData']['CustomerEndpoint']['Address']
    InstanceARN=event['Details']['ContactData']['InstanceARN']
    InstanceId = InstanceARN[-36:]

    client = boto3.client('connect')
    
    Name=requestType.upper()
    URL="https://www.your-internet-on-demand.com/?accountNumber="+accountNumber
    Description="Request type ="+requestType+". AccountNumber="+ accountNumber+". Caller number="+CLID
    
    
    response = client.start_task_contact(
        InstanceId=InstanceId,
        ContactFlowId='4517729d-21e7-4d3a-8a28-c96f881aa3c3',
        Name=Name,
        References={
            'URL': {
                'Value': URL,
                'Type': 'URL'
            }
        },
        Description=Description
    )
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
