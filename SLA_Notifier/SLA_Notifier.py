import json
import boto3
from botocore.exceptions import ClientError

from datetime import date, datetime, time, timedelta

def ceil_dt(dt, delta):
    return dt + (datetime.min - dt) % delta



# function that gets SLA for queue using Amazon Connect API
def getSLA(_InstanceId,statInterval,channel,queueID,Threshold):
    
    now = datetime.now()
    end=ceil_dt(now, timedelta(minutes=5))

    start = end - timedelta(hours=0, minutes=int(statInterval))

    client = boto3.client('connect')    

    response = client.get_metric_data(
            InstanceId=_InstanceId,
            StartTime=start,
            EndTime=end,
            Filters={
                    'Queues': [
                        queueID,
                    ],
                    'Channels': [
                        channel,
                    ]
                },
                HistoricalMetrics=[
                    {
                        'Name': 'SERVICE_LEVEL',
                        'Statistic': 'AVG',
                        'Unit': 'PERCENT',
                        'Threshold': 
                            { 
                                "Comparison": "LT",
                                 "ThresholdValue": Threshold
                             },
                    },
                ]
        )

    metric_results_list=response['MetricResults']
    metric_results_dict=metric_results_list[0]
    collections_list=metric_results_dict['Collections']
    count=len(collections_list)
    if count>0:
        collections_dict=collections_list[0]
        value=collections_dict['Value']
    else:
        value="0"
    
    return value
    

# function that sends SMS using Amazon SNS
def sendSMS(message, phoneNumber,_region_name):
    
    client = boto3.client("sns",region_name=_region_name)
            
    client.publish(
            PhoneNumber=phoneNumber,
            Message=message
    )
    
    return {
                    'statusCode': 200,
                    'body': json.dumps('OK')
    }

# function that sends email using Amazon SES
def sendEmail(MailFrom, MailTo,Body_TEXT,Body_HTML,Subject,_region_name):

    CHARSET = "UTF-8"
    client = boto3.client('ses',region_name=_region_name)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    MailTo,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': Body_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': Body_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': Subject,
                },
            },
            Source=MailFrom,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('OK')
        }


# function that grabs all data from DynamoDB table
def dump_table(table_name):
    
    client = boto3.client('dynamodb')
    
    results = []
    last_evaluated_key = None
    while True:
        if last_evaluated_key:
            response = client.scan(
                TableName=table_name,
                ExclusiveStartKey=last_evaluated_key
            )
        else: 
            response = client.scan(TableName=table_name)
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        results.extend(response['Items'])
        
        if not last_evaluated_key:
            break
    return results
    
def lambda_handler(event, context):
    
    
    # Amazon Connect InstanceId
    InstanceId="838ab265-dd60-476b-976c-0ce5fac44809"
    
    #Statistical interval in minutes
    statInterval="60"
    
    # Region name of Amazon SES and Amazon SNS
    region_name="us-east-1"
    
    # MailFrom for EMail notification
    MailFrom = "sla_notifier@ecorp.com"
    
    # Subject for EMail notifications
    Subject='SLA Notifier'


    data = dump_table('SLA_Notifier')
    
    for item in data:
        phoneNumber=item["phoneNumber"]["S"]
        email=item["email"]["S"]
        QueueId=item["QueueId"]["S"]
        QueueName=item["QueueName"]["S"]
        SendSMS=item["SendSMS"]["S"]
        SendEmail=item["SendEmail"]["S"]
        Threshold=item["Threshold"]["S"]
        Channel=item["Channel"]["S"]
        SLA=getSLA(InstanceId,statInterval,Channel,QueueId,int(Threshold))
        if SendSMS=="yes":
            message="Queue: "+QueueName+"\r\n"+"SL_20: "+ str(SLA)+'%'
            sendSMS_result=sendSMS(message,phoneNumber,region_name)
        if SendEmail=="yes":
            Body_TEXT="Queue: "+QueueName+"\r\n"+"SL_20: "+ str(SLA)+'%'
            Body_HTML="Queue: "+QueueName+"<br>"+"SL_20: "+ str(SLA)+'%'
            sendEmail_result=sendEmail(MailFrom,email,Body_TEXT,Body_HTML,Subject,region_name)

