import json
from datetime import datetime
import sys
from pip._internal import main

#this is to make sure that we always get latest boto3 library
main(['install', '-I', '-q', 'boto3', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')

import boto3
from botocore.exceptions import ClientError

# function that returns list of Amazon Connect users
def getUserList(instance_id):
  
	client = boto3.client('connect')
	
    #API only allows to fetch up to 1000 users at once. 
    #After that we will use NextToken to get next batch
    MaxResults = 1000
    
    users_all = ''
    
	#get list of Amazon Connect users - first batch
	response = client.list_users(
    	InstanceId=instance_id,
    	MaxResults=MaxResults
    )

	users=response['UserSummaryList']
	users_all = [*users_all,*users]
    
    #next batch
	while True:
		if ("NextToken" in response) == True:
    
			NextToken=response['NextToken']

			response = client.list_users(
            	InstanceId=instance_id,
    	        NextToken=NextToken,
    	        MaxResults=MaxResults
            )
        
			users=response['UserSummaryList']
			users_all = [*users_all,*users]
          
		else:
			break
    
	return users_all

def lambda_handler(event, context):
	
	#Amazon Connect InstanceID
	instance_id="513ab265-dd50-476b-976c-0ce5fac49907"
	
	# get current datetime (UTC)
	now = datetime.now()
	dt_string = now.strftime("%Y_%m_%d__%H_%M_%S")
	
	
	#Headers for our CSV-file
	headers="id,username,firstname,lastname,email,phonetype,autoaccept,acw_timeout,desk_number,security_profiles,hierarchy_group_name,routing_profile_name,routing_profile_concurrency,routing_profile_outbound_queue_name,routing_profile_details_list"+"\r\n"
	
	#csv-file name
	csv_file='/tmp/amazon_connect_users__'+dt_string+'.csv'
	
	#S3 bucket name
	s3_bucket='amazon-connect-export'
	
	s3 = boto3.client('s3')
	data_file = open(csv_file, 'w+')
	data_file.write(headers)

	
	client = boto3.client('connect')  
    
	#get list of Amazon Connect users
	users=getUserList(instance_id)
	
	for user in users:
		user_id=user['Id']
		user_name=user['Username']
		response=client.describe_user(
			InstanceId=instance_id,
			UserId=user_id
		)
		user_firstname=response['User']['IdentityInfo']['FirstName']
		user_lastname=response['User']['IdentityInfo']['LastName']
		user_email=response['User']['IdentityInfo']['Email']
		user_phonetype=response['User']['PhoneConfig']['PhoneType']
		user_autoaccept=response['User']['PhoneConfig']['AutoAccept']
		user_acw_timeout=response['User']['PhoneConfig']['AfterContactWorkTimeLimit']
		user_desk_number=response['User']['PhoneConfig']['DeskPhoneNumber']
		user_routing_profile_id=response['User']['RoutingProfileId']
		user_hierarchy_group_id=response['User']['HierarchyGroupId']
		user_security_profile_ids=response['User']['SecurityProfileIds']
		
		security_profile_name_list=''
		for security_profile_id in user_security_profile_ids:
			security_profile = client.describe_security_profile(
				 SecurityProfileId=security_profile_id,
				 InstanceId=instance_id
			)
			security_profile_name=security_profile['SecurityProfile']['SecurityProfileName']
			security_profile_name_list=security_profile_name_list+'|'+security_profile_name
		
		routing_profile=client.describe_routing_profile(
			InstanceId=instance_id,
			RoutingProfileId=user_routing_profile_id
		)
		
		routing_profile_id=routing_profile['RoutingProfile']['Name']
		routing_profile_name=routing_profile['RoutingProfile']['Name']
		routing_profile_outbound=routing_profile['RoutingProfile']['DefaultOutboundQueueId']
		routing_profile_chat=routing_profile['RoutingProfile']['MediaConcurrencies'][0]['Concurrency']
		routing_profile_task=routing_profile['RoutingProfile']['MediaConcurrencies'][1]['Concurrency']
		routing_profile_voice=routing_profile['RoutingProfile']['MediaConcurrencies'][2]['Concurrency']
		routing_profile_concurrency=str(routing_profile_chat)+"|"+str(routing_profile_task)+"|"+str(routing_profile_voice)
		
		
		routing_profile_outbound_queue = client.describe_queue(
			 InstanceId=instance_id,
    		 QueueId=routing_profile_outbound
		)
		
		routing_profile_outbound_queue_name=routing_profile_outbound_queue['Queue']['Name']
		
		routing_profile_queues = client.list_routing_profile_queues(
		    InstanceId=instance_id,
		    RoutingProfileId=user_routing_profile_id,
		    MaxResults=100
		)
		
		routing_profile_queues_list=routing_profile_queues['RoutingProfileQueueConfigSummaryList']
		
		routing_profile_details_list=''
		for routing_profile_queue in routing_profile_queues_list:
			routing_profile_details=routing_profile_queue['QueueName']+"|"+str(routing_profile_queue['Priority'])+"|"+str(routing_profile_queue['Delay'])+"|"+routing_profile_queue['Channel']
			
			routing_profile_details_list=routing_profile_details_list+';'+routing_profile_details
		
		
		hierarchy_group=client.describe_user_hierarchy_group(
			InstanceId=instance_id,
			HierarchyGroupId=user_hierarchy_group_id
		)
		
		hierarchy_group_name=hierarchy_group['HierarchyGroup']['Name']
		
		user_info="'"+user_id+"','"+user_name+"','"+user_firstname+"','"+user_lastname+"','"+user_email+"','"+user_phonetype+"','"+str(user_autoaccept)+"','"+str(user_acw_timeout)+"','"+user_desk_number+"','"+security_profile_name_list[1:]+"','"+hierarchy_group_name+"','"+routing_profile_name+"','"+routing_profile_concurrency+"','"+routing_profile_outbound_queue_name+"','"+routing_profile_details_list[1:]+"'\r\n"
		
	
		data_file.write(user_info)
		

	data_file.close()
	

	#upload CSV file to S3
	s3.upload_file(csv_file, s3_bucket , csv_file)
