import json
import boto3

from datetime import date, datetime, time, timedelta

def ceil_dt(dt, delta):
    return dt + (datetime.min - dt) % delta

def lambda_handler(event, context):
    
    # let's try to get statInterval attribute from the contact. If it is not found we will use 15 minutes as default value.
    attributes=event['Details']['ContactData']['Attributes']
    if ("statInterval" in attributes) == True:
        statInterval=attributes['statInterval']
    else:
        statInterval=15
    

    channel=event['Details']['ContactData']['Channel']
    queueARN=event['Details']['ContactData']['Queue']['ARN']
    queueID = queueARN[-36:]
    
    InstanceARN=event['Details']['ContactData']['InstanceARN']
    InstanceId=InstanceARN[-36:]
    
    now = datetime.now()
    end=ceil_dt(now, timedelta(minutes=5))

    start = end - timedelta(hours=0, minutes=int(statInterval))

    client = boto3.client('connect')    

    response = client.get_metric_data(
            InstanceId=InstanceId,
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
                        'Name': 'QUEUE_ANSWER_TIME',
                        'Statistic': 'AVG',
                        'Unit': 'SECONDS'
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
        
    resultMap = {"EWT":value}
    return resultMap