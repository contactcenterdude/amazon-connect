import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Clients')
    
    CLID=event['Details']['ContactData']['CustomerEndpoint']['Address']
   
    
    response = table.query(
        KeyConditionExpression=Key('phoneNumber').eq(CLID)
        )
    resp=response['Items']
    
    for item in resp:
            Email=item['Email']
    

    MailFrom = "support@yourcompany.com"
    MailTo = Email
    MailSubject = "New application instructions"
    
    # Non-HTML Body
    MailBody = ("New application instructions\r\n"
                 "Access following link to get installation instructions http://tinyurl.com/AmazonConnectSMS"             
                )
                
    # HTML Body
    MailBodyHTML = """<html>
    <head></head>
    <body>
      <h1>New application instrunctions</h1>
      <p>Access following link to get installation instructions
        <a href='http://tinyurl.com/AmazonConnectSMS'>New application</a>
        </p>
    </body>
    </html>
    """            
    
 
    client = boto3.client('ses',region_name="us-east-1")

    # Sending email
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    MailTo,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': "UTF-8",
                        'Data': MailBodyHTML,
                    },
                    'Text': {
                        'Charset': "UTF-8",
                        'Data': MailBody,
                    },
                },
                'Subject': {
                    'Charset': "UTF-8",
                    'Data': MailSubject,
                },
            },
            Source=MailFrom,
        )
 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return {
            'statusCode': 200,
            'body': json.dumps('OK')
        }
