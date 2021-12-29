import json
from datetime import datetime
import sys
from pip._internal import main

#this is to make sure that we always get latest boto3 library
main(['install', '-I', '-q', 'boto3', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
	
	#Amazon Connect InstanceID
	instance_id="896ab265-dd50-476b-976c-0ce5fac38451"
	
	# get current datetime (UTC)
	now = datetime.now()
	dt_string = now.strftime("%Y_%m_%d__%H_%M_%S")
	
	
	#Headers for our CSV-file
	headers="id,name,desc,status,hours,ob_callerid_name,ob_phonenumber,ob_flow"+"\r\n"
	
	#csv-file name
	csv_file='/tmp/amazon_connect_queues__'+dt_string+'.csv'
	
	#S3 bucket name
	s3_bucket='amazon-connect-export'
	
	s3 = boto3.client('s3')
	data_file = open(csv_file, 'w+')
	data_file.write(headers)

	
	client = boto3.client('connect')  

	#get list of Amazon Connect queues
	response = client.list_queues(
		InstanceId=instance_id,
		MaxResults=1000,
		QueueTypes=[
        'STANDARD',
    	],
	)
	
	queues_list=response['QueueSummaryList']
	
	for queue in queues_list:
		queue_id=queue['Id']

		queue_details = client.describe_queue(
			 InstanceId=instance_id,
    		 QueueId=queue_id
		)
		
		queue_name=queue_details['Queue']['Name']
		queue_desc=queue_details['Queue']['Description']
		queue_status=queue_details['Queue']['Status']
		queue_hours_id=queue_details['Queue']['HoursOfOperationId']
	
		
		hours = client.describe_hours_of_operation(
    		 InstanceId=instance_id,
			 HoursOfOperationId=queue_hours_id
		)
		
		hours_name=hours['HoursOfOperation']['Name']
		
		queue_ob_config=queue_details['Queue']['OutboundCallerConfig']

		if ("OutboundCallerIdName" in queue_ob_config) == True:
			queue_ob_callerid_name=queue_ob_config['OutboundCallerIdName']
		else:
			queue_ob_callerid_name=''
		
		if ("OutboundCallerIdNumberId" in queue_ob_config) == True:
			queue_ob_callerid_number_id=queue_ob_config['OutboundCallerIdNumberId']
			
			phone_numbers_list=client.list_phone_numbers(
				InstanceId=instance_id
			)
			
			for phone_number in phone_numbers_list['PhoneNumberSummaryList']:
				phone_number_id=phone_number['Id']
				if phone_number_id == queue_ob_callerid_number_id:
					phone_number_tel=phone_number['PhoneNumber']
		else:
			queue_ob_callerid_number_id=''
			phone_number_tel=''
		
		
			
		if ("OutboundFlowId" in queue_ob_config) == True:
			queue_ob_flow_id=queue_ob_config['OutboundFlowId']
			
			queue_ob_flow = client.describe_contact_flow(
				 InstanceId=instance_id,
    			 ContactFlowId=queue_ob_flow_id
			)
			queue_ob_flow_name=queue_ob_flow['ContactFlow']['Name']
			
		else:
			queue_ob_flow_id=''
		
		queue_info="'"+queue_id+"','"+queue_name+"','"+queue_desc.replace(",","")+"','"+queue_status+"','"+hours_name+"','"+queue_ob_callerid_name+"','"+phone_number_tel+"','"+queue_ob_flow_name+"'\r\n"
	
		data_file.write(queue_info)
		

	data_file.close()
	

	#upload CSV file to S3
	s3.upload_file(csv_file, s3_bucket , csv_file)
