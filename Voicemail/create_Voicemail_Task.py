import logging
import math
import json 
import boto3
import urllib.request
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone


# find username associated with agentId
def getVMAgent(agentId,VoicemailTable):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(VoicemailTable)
    
  
    response = table.query(
            KeyConditionExpression=Key('agentId').eq(agentId)
       )
    resp=response['Items']
    
    try:    
        for item in resp:
            username=item['username']

        return username 
        
    except ClientError as e:
        print(e.response['Error']['Message'])


#get text of voicemail transcript
def getTranscript(TranscriptionJobName,region_name): 
        
        client = boto3.client("transcribe",region_name)
        response = client.get_transcription_job(
             TranscriptionJobName=TranscriptionJobName
        )
        
        transcriptURL=response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
 
        with urllib.request.urlopen(transcriptURL) as url:
            data = json.loads(url.read().decode())
            transcript=data["results"]["transcripts"][0]["transcript"]
            return transcript


#find QueueID by QueueName
def findQueueIDbyName(instance_id,QueueName):

	client = boto3.client('connect')   
	

	
	response = client.list_queues(
		InstanceId=instance_id,
		MaxResults=1000
	)
	
	
	queues_id_list=response['QueueSummaryList']

	
	for queue_id in queues_id_list:
		_id=queue_id['Id']
		try:
			response = client.describe_queue(
				InstanceId=instance_id,
				QueueId=_id
				)
			_QueueName=response['Queue']['Name']
			if QueueName==_QueueName:
				return _id
		except:
			pass
			

#create Amazon Connect task
def initiateTask(InstanceId, ContactFlowId,TaskName,TaskDescription,TaskURL,contactPhoneNumber,transcript,QueueName,QueueID,task_dt):
    

    client = boto3.client('connect')
    
    Name=TaskName
    
    response = client.start_task_contact(
        InstanceId=InstanceId,
        ContactFlowId=ContactFlowId,
        Name=TaskName,
        References={
            'Listen to Voicemail': {
                'Value': TaskURL,
                'Type': 'URL'
            }
        },
        Description=TaskDescription,
        Attributes={
          'contactPhoneNumber': contactPhoneNumber,
          'Voicemail_Transcript':transcript,
          'QueueName':QueueName,
          'QueueID':QueueID,
          'Datetime':task_dt
        },
    )
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }


def lambda_handler(event, context):

    # Region name of Amazon S3 and Amazon Transcribe
    region_name="us-east-1"
    
    # Amazon Connect InstanceId
    InstanceId="818ab265-dd50-476b-446c-0ce5fac38807"
    
    # FlowId of SendTask flow 
    ContactFlowId='5b67729d-21e7-4d3c-8a28-c96f881aa1a1'
    
    #name of DynamoDB table that is used by Voicemail to store voicemail users
    VoicemailTable="Amazon-Connect-Voicemail-VoicemailStack-1O9JZHZJ8ZD7Y-UsersTable-4DLIYWATXZ7T"
    
    records=event["Records"]
    for record in records:
        transcribeStatus=""
        
        # get status of transciption job
        transcribeStatus=record["dynamodb"]["NewImage"]["transcribeStatus"]["S"]

        contactPhoneNumber=""
        recordingUrl=""
        contactId=""
        assigneeId=""
        recordingBucketName=""
        recordingObjectKey=""
        username=""
        QueueName=""
        QueueID=""
        TranscriptionJobName=""
        transcript=""
        TaskDescription=""
        TaskURL=""
        task_dt=""

        # if transcription is completed - we will start generating Task
        if transcribeStatus=="COMPLETED":
            
            # get all available info about voicemail/transcription
            contactPhoneNumber=record["dynamodb"]["NewImage"]["contactPhoneNumber"]["S"]
            recordingUrl=record["dynamodb"]["NewImage"]["recordingUrl"]["S"]
            timestamp=record["dynamodb"]["NewImage"]["timestamp"]["N"]
            contactId=record["dynamodb"]["NewImage"]["contactId"]["S"]
            assigneeId=record["dynamodb"]["NewImage"]["assigneeId"]["S"]
            recordingBucketName=record["dynamodb"]["NewImage"]["recordingBucketName"]["S"]
            recordingObjectKey=record["dynamodb"]["NewImage"]["recordingObjectKey"]["S"]
            
            #need to find real username by id
            username=getVMAgent(assigneeId,VoicemailTable)
            
            # username has following format VM.QueueName
            QueueName=username[3:]
            
            # need to get QueueID using QueueName
            QueueID=findQueueIDbyName(InstanceId,QueueName)
            
            # need to get voicemail transcript from Amazon Transcribe
            TranscriptionJobName=contactId+"_"+timestamp
            transcript=getTranscript(TranscriptionJobName,region_name)
    
            TaskName="Voicemail"
            TaskDescription="Voicemail from "+contactPhoneNumber
            
            #convert epoch time to UTC datetime
            task_dt=str(datetime.fromtimestamp(int(timestamp), timezone.utc))+" UTC"
                    
            #generate presigned URL that will be valid for 7 days
            TaskURL = boto3.client('s3').generate_presigned_url(
            ClientMethod='get_object', 
            Params={'Bucket': recordingBucketName, 'Key': recordingObjectKey},
            ExpiresIn=604800)
          
            #create Amazon Connect Task
            initiateTask(InstanceId,ContactFlowId,TaskName,TaskDescription,TaskURL,contactPhoneNumber,transcript,QueueName,QueueID,task_dt)

