import json
import boto3

def lambda_handler(event, context):
    

    QueueARN=event['Details']['ContactData']['Queue']['ARN']
    QueueID=QueueARN[-36:]
       
    Channel=event['Details']['ContactData']['Channel']
 
    
    InstanceARN=event['Details']['ContactData']['InstanceARN']
    InstanceId=InstanceARN[-36:]
    
    client = boto3.client('connect')   
    
    response = client.get_current_metric_data(
                InstanceId=InstanceId,
                Filters={
                    'Queues': [
                        QueueID,
                    ],
                    'Channels': [
                        Channel,
                    ]
                },
                Groupings=[
                    'QUEUE',
                ],
                CurrentMetrics=[
                    {
                        'Name': 'AGENTS_STAFFED',
                        'Unit': 'COUNT'
                    },
                    {
                        'Name': 'AGENTS_ERROR',
                        'Unit': 'COUNT'
                    }
                ]
                )
    
    agents_staffed=response['MetricResults'][0]['Collections'][0]['Value']
    agents_error=response['MetricResults'][0]['Collections'][1]['Value']
    agents_in_service=agents_staffed-agents_error
    
    if agents_in_service>0:
        Queue_In_Service=False
    else:
        Queue_In_Service=True
   
    print(Queue_In_Service)     
    resultMap = {"OOS":Queue_In_Service}
    return resultMap
    