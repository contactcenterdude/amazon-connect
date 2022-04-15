###Enter InstanceID of your Amazon Connect
$instance_id="715ab265-dd70-476b-876c-0ce5fa838877"


###Export full list of UserIDs
$user_id_list = Get-CONNUserList -InstanceId $instance_id| Select-Object -First 1000 @('Id')


###Export full list of Security Profiles
$security_profiles_list=Get-CONNSecurityProfileList -InstanceId $instance_id | Select-Object @('Id','Name')


#Path to CSV file with exported info
$ExportPath = "c:\Temp\AWS_Connect_users.csv"


###Prepare CSV-header
$csv_header='id,username,EMail,FirstName,LastName,PhoneType,DeskPhoneNumber,AutoAccept,ACW,RoutingProfile,Hierarchy,SecurityProfiles' | Out-File $ExportPath


###get info about each individual user in the list
Foreach ($i in $user_id_list)
{
  ###get user info by ID
  $user_info=Get-CONNUser -UserId $i.Id -InstanceId $instance_id 


  ###get info about Routing profile assigned to user
  $routing_profile= Get-CONNRoutingProfile -InstanceId $instance_id -RoutingProfileId $user_info.RoutingProfileId


  ###get info about Hierarchy assigned to user
  if($user_info.HierarchyGroupId -eq $null){
  $user_hierarchy=''
  } else {
  $user_hierarchy= Get-CONNUserHierarchyGroup -HierarchyGroupId $user_info.HierarchyGroupId  -InstanceId $instance_id
  }


  ###get list of security profiles assigned to user
  $user_roles=''
  Foreach ($s in $security_profiles_list)
  {   
     if($user_info.SecurityProfileIds -match $s.id){$user_roles=$user_roles+'|'+$s.Name}   
  }
 


    
  ###Prepare CSV

  $user_description=$user_info.id+','+$user_info.username+','+$user_info.IdentityInfo.Email+','+$user_info.IdentityInfo.FirstName+','+  $user_info.IdentityInfo.LastName
  $user_description=$user_description+','+$user_info.PhoneConfig.PhoneType.Value+','+$user_info.PhoneConfig.DeskPhoneNumber+','+$user_info.PhoneConfig.AutoAccept+','+$user_info.PhoneConfig.AfterContactWorkTimeLimit
  $user_description=$user_description+','+$routing_profile.Name+','+$user_hierarchy.Name+','+$user_roles.Substring(1)
  
  $user_description | Out-File $ExportPath -Append
}
