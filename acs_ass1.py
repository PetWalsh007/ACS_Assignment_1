#!/usr/bin/env python3

'''

- Peter Walsh - 20098070 - Year 4 Automation Engineering - Created @ 18/02/2025 -

Please see github readme.md for notes on this assignment:
https://github.com/PetWalsh007/ACS_Assignment_1

'''


import boto3
import logging
import time
import random
import sys
import requests
import os
import string
import json
import subprocess
from time import sleep

##---------##
## Declarations and Global Variables ##
# https://docs.python.org/3/library/logging.html - 
log_format ="%(asctime)s - %(message)s"
logging.basicConfig(filename="PWalsh-ACS-log-Assignment1", level=logging.INFO, format=log_format)

# ec2 initalisation 
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# s3 initalisation
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

# bucket name for s3 bucket creation - https://www.geeksforgeeks.org/python-generate-random-string-of-given-length/ 
str_lenght = 6
bucket_name_s3 = ''.join(random.choices(string.ascii_letters + string.digits, k=str_lenght))
bucket_name_s3 = bucket_name_s3 + '-pwalsh'
bucket_name_s3 = bucket_name_s3.lower()

# image download url and file name
img_dwl_url = "https://setuacsresources.s3-eu-west-1.amazonaws.com/image.jpeg"
img_file_name = "image_SETU_ACS.jpeg"


# Security Group ID created for this assignment - which allows http and ssh access
sg_id = 'sg-0c460c49e45787055'

# Instance key pair name - created and used for this assignment
key_pair_name = 'First_key_pair_ACS'

# Instance ami image id - Amazon Linux 2023 
ami_id = 'ami-053a45fff0a704a47'

# tag name for the instance - # time will allow us to sort by name using timestamp
tag_name = f'{time.strftime("%d%m%y%H%M%S")}_PWalsh_ACS_Assignment1' 
current_time = time.strftime("%Y-%m-%d%H%M%S")
created_ami_name =f'PW-{current_time}'

monitoring_file = 'monitoring.sh'

ec2_user_name = 'ec2-user'

##---------##


def create_ec2_instance():
    console_logging('info', f"Creating \033[1mEC2 instance\033[0m with tag name: \033[1m{tag_name}\033[0m")
    global instance_ip_addr
    global instance
    

    try:
        instance = ec2.create_instances(
            ImageId = ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType = 't2.nano',
            KeyName = key_pair_name,
            SecurityGroupIds = [sg_id],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name','Value': tag_name}
                            ]
                },
            ],
            UserData = get_userdata_file()
            )
        
    except Exception as error:
        console_logging('error', f"Error while creating instance: {error}")
        
   # Wait until the instance is running to get the ip address and updated instance info
    try:
        console_logging('info', "Waiting for instance to be running")
        instance[0].wait_until_running() # wait until running to obtain ip address
        instance[0].reload() # Reload to get new info
        instance_ip_addr = instance[0].public_ip_address
        console_logging('info', f"Instance ID: {instance[0].id}")
        console_logging('info', f"Instance IP Address: {instance_ip_addr}")
        console_logging('info', f"Instance State: {instance[0].state['Name']}")
        console_logging('info', f"Instance Key Pair: {instance[0].key_name}")
        console_logging('info', f"Instance Security Group: {instance[0].security_groups[0]['GroupId']}")
    except Exception as error:
        console_logging('error', f"Error while getting instance info: {error}")


    ec2_instance_web_url = f"http://{instance_ip_addr}"
    console_logging('info', f"Instance is now available at \033[1m{ec2_instance_web_url}\033[0m")

    return ec2_instance_web_url
    



def get_userdata_file():
    return '''#!/bin/bash
                    yum update -y
                    yum install httpd -y
                    systemctl enable httpd
                    systemctl start httpd
                    TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` 
                    echo "<h2>Test page</h2>Instance ID: " > /var/www/html/index.html
                    curl --silent -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id/ >> /var/www/html/index.html
                    echo "<br>Availability zone: " >> /var/www/html/index.html 
                    curl --silent -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone/ >> /var/www/html/index.html
                    echo "<br>IP address: " >> /var/www/html/index.html
                    curl --silent -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 >> /var/www/html/index.html
                '''


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/create_image.html
def create_ami():
    global created_ami_id

    console_logging('info', f"Begining to create new AMI with tag name: {created_ami_name}")

    try:
        response = ec2_client.create_image(TagSpecifications=[{
                                                            'ResourceType': 'image',
                                                            'Tags':[
                                                                {
                                                                    'Key': 'Name','Value': created_ami_name
                                                                },
                                                            ]
                                                        }],
        Description='An AMI for ACS Assignment 1 - Peter Walsh',
        InstanceId = instance[0].id,
        Name = created_ami_name,
        )
        created_ami_id = response['ImageId']
        console_logging('info', f"AMI ID: {response['ImageId']}")
    except Exception as error:
        console_logging('error', f"Error while creating AMI: {error}")

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_images.html
    
    response = ec2_client.describe_images(ImageIds=[
                                                created_ami_id,
                                            ],
    )

 
    try:
        response = response['Images'][0]['State']
        console_logging('info', f"AMI State: {response}")
    except Exception as error:
        console_logging('error', f"Error while getting AMI state: {error}")


    pass

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
def create_s3_bucket():
    console_logging('info', f"Creating \033[1mS3 bucket: {bucket_name_s3}\033[0m")
    try:
        response = s3.create_bucket(Bucket=bucket_name_s3)
        if response:
            console_logging('info', f"S3 bucket {bucket_name_s3} created successfully")
    except Exception as error:
        console_logging('error', f"Error while creating S3 bucket: {error}")

    # Removed public access block to allow public access to the bucket
    console_logging('info', f"Removing public access block from {bucket_name_s3}")
    try:
        s3_client.delete_public_access_block(Bucket=bucket_name_s3) # need to use s3 client to remove public access block 
    except Exception as error:
        console_logging('error', f"Error while removing public access block: {error}")

    # Updated bucket policy to allow public access to the bucket
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [{
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": ["s3:GetObject"],
        "Resource": [
                f"arn:aws:s3:::{bucket_name_s3}/*"]}
            ]

        }
    
    try:
        s3.Bucket(bucket_name_s3).Policy().put(Policy=json.dumps(bucket_policy))
    except Exception as error:  
        console_logging('error', f"Error while updating bucket policy: {error}")



    pass

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-static-web-host.html
def make_s3_static():
    console_logging('info', f"Making \033[1m{bucket_name_s3}\033[0m a static website host")
    website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
    }

    try:
        bucket_website = s3.BucketWebsite(bucket_name_s3)
        bucket_website.put(WebsiteConfiguration=website_configuration)
        console_logging('info', f"{bucket_name_s3} is now a static website host")
    except Exception as error:
        console_logging('error', f"Error while making {bucket_name_s3} a static website host: {error}")
    


    pass



def get_html_data(): 
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ACS Assignment 1 - Peter Walsh</title>
    </head>
    <body>
    <img src="{object}" />
    <h1>Peter Walsh 20098070</h1>
    </body>
    </html>
    '''
   

def get_image():
    # https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions - request documentation for error handling
    console_logging('info', f"Downloading image from {img_dwl_url}")
    try:
        img_resource = requests.get(img_dwl_url)
        if img_resource.status_code != 200:
            console_logging('error', f"Error while downloading image: {img_resource.status_code}")
        elif img_resource.status_code == 200:
            console_logging('info', f"Image downloaded successfully")
        else:
            console_logging('error', f"Error while downloading image: {img_resource.status_code}")
    except requests.exceptions.RequestException as e:
        console_logging('error', f"Error while downloading image: {e}")

   
    try:
        with open(img_file_name, "wb") as f:
            f.write(img_resource.content)
        console_logging('info', f"Image saved as {img_file_name}")
    except Exception as error:
        console_logging('error', f"Error while saving image: {error}")


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
def upload_to_s3():
    global object
    object = img_file_name
    file_type = '.' + object.split(".")[1]
    object = object.split(".")[0] + '_pwalsh' + file_type
    console_logging('info', f"Uploading image file to {bucket_name_s3}")

    try:
        with open(img_file_name, "rb") as img:
            s3_client.put_object(Bucket=bucket_name_s3, Key=object, Body=img, ContentType='image/jpeg') # uploads the image file to the bucket and set the content type to image/jpeg
            console_logging('info', f"Image file uploaded to {bucket_name_s3}")
    except Exception as error:
        console_logging('error', f"Error while uploading image: {error}")

    
    console_logging('info', f"Uploading \033[1mindex.html\033[0m to \033[1m{bucket_name_s3}\033[0m")
    html_index_data = get_html_data() # calls the get_html_data function to get the html data
    try:
        s3_client.put_object(Bucket=bucket_name_s3, Key='index.html', Body=html_index_data, ContentType='text/html') # uploads the index.html file to the bucket and set the content type to html
        console_logging('info', f"index.html uploaded to {bucket_name_s3}")
    except Exception as error:
        console_logging('error', f"Error while uploading index.html: {error}")

    s3_website_url = f"http://{bucket_name_s3}.s3-website-us-east-1.amazonaws.com"
    console_logging('info', f"Website Available at \033[1m{s3_website_url}\033[0m")

    return s3_website_url

    



def console_logging(type, m_info, flag=True):

    if flag:
        if type == 'info':
            print(f"INFO: {m_info}")
            logging.info(f"INFO: {m_info}")
        elif type == 'error':
            print(f"ERROR: {m_info}")
            logging.error(f"ERROR: {m_info}")
            program_error() # call program error function to clean up resources and exit
        elif type == 'debug':
            print(f"DEBUG: {m_info}")
            logging.debug(f"DEBUG: {m_info}")
        else:
            print(f"{m_info}")
            logging.error(f"Error: {m_info}")
    elif flag == False:
        print(f"Error: {m_info} - False Flag Captured - Exiting Program State")   
        logging.error(f"Error: {m_info} - False Flag Captured - Exiting Program State") 
    pass


def get_ipt_args():
# Function to take the input arguments from the user to determine if cleanup is required after the script has run

    global cleanup
    global wait_time
    cleanup = False
    wait_time = 0
    
    if len(sys.argv) > 1:
        sys.argv[1] = sys.argv[1].upper() # convert to uppercase to avoid case sensitivity
        if sys.argv[1] == 'TRUE':
            cleanup = True
            console_logging('info', "\033[1mCleanup flag detected. Script will remove all resources after script completion\033[0m")
            if len(sys.argv) > 2 and int(sys.argv[2]) > 0:
                wait_time = int(sys.argv[2])
                console_logging('info', f"Wait time set to {wait_time} seconds post script completion")
            else:
                wait_time = 60 # default wait time 
                console_logging('info', f"Wait time set to defualt {wait_time} seconds post script completion")
        elif sys.argv[1] == 'FALSE':
            console_logging('info', "No cleanup flag detected. Script will not remove resources after script completion")

        else:
            console_logging('info', "No cleanup flag detected. Script will not remove resources after script completion")




def cleanup_resources():
    # Cleanup function to remove all resources created during the script execution 
    # Note - flag here is set to false to avoid the program error function from being called recursively
    global cleanup_jobs
    cleanup_jobs ={ 's3_bucket': False, 'ec2_instance': False, 'ami': False}

    console_logging('info', f"Cleaning up resources after {wait_time} seconds")
    time.sleep(wait_time/2)
    console_logging('info', f"Cleaning up resources in {round(wait_time/2, 0)} seconds")
    time.sleep(wait_time/2)
    console_logging('info', "Cleaning up resources in progress")
    # Empty S3 bucket
    console_logging('info', f"Emptying bucket: {bucket_name_s3}")
    try:
        bucket = s3.Bucket(bucket_name_s3)
        for obj in bucket.objects.all():
            try:
                obj.delete()
                console_logging('info', f"Deleted object: {obj.key}")
            except Exception as error:
                console_logging('error', f"Error while deleting object: {error}", False)
        console_logging('info', f"Bucket {bucket_name_s3} is now empty")
    except Exception as error:
        console_logging('error', f"Error while emptying bucket: {error}", False)
    
    # Delete S3 bucket
    console_logging('info', f"Deleting bucket: {bucket_name_s3}")
    try:
        s3_client.delete_bucket(Bucket=bucket_name_s3)
        console_logging('info', f"Deleted bucket: {bucket_name_s3}")
        cleanup_jobs['s3_bucket'] = True
    except Exception as error:
        console_logging('error', f"Error while deleting bucket: {error}", False)

    # Terminate EC2 instance
    console_logging('info', f"Terminating instance: {instance[0].id}")
    try:
        instance[0].terminate()
        instance[0].wait_until_terminated()
        console_logging('info', f"Terminated instance: {instance[0].id}")
        cleanup_jobs['ec2_instance'] = True
    except Exception as error:
        console_logging('error', f"Error while terminating instance: {error}", False)

    # Deregister AMI - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/deregister_image.html 
    console_logging('info', f"Deregistering AMI: {created_ami_id}")
    try:
        ec2_client.deregister_image(ImageId=created_ami_id)
        console_logging('info', f"Deregistered AMI: {created_ami_id}")
        cleanup_jobs['ami'] = True
    except Exception as error:
        console_logging('error', f"Error while deregistering AMI: {error}", False)

    
    console_logging('info', "Cleanup complete")
    pass


def program_error():
    cleanup_resources()
    console_logging('error', "Starting Exit of Program due to error in script", False)
    for job in cleanup_jobs:
        console_logging('info', f"Status of removal post cleanup job: {job} - {'Success' if cleanup_jobs[job] else 'Failed'}")
    sys.exit(1)
    pass

def write_to_file(ec2_url, s3_url):
    # Function to write the EC2 and S3 URLs to a file
    
    file_name = 'pwalsh-websites.txt'
    console_logging('info', f"Writing URLs to file: {file_name}")
    try:
        with open(file_name, 'w') as f:
            f.write(f"EC2 URL: {ec2_url}\n")
            f.write(f"S3 URL: {s3_url}\n")
            console_logging('info', f"URLs written to file: \033[1m{file_name}\033[0m")
    except Exception as error:
        console_logging('error', f"Error while writing URLs to file: {error}")




def upload_run_monitoring():
    # function to upload monitoring script to the instance created
    console_logging('info', f"Uploading monitoring script to instance: {instance[0].id}")

    try:
        # build connection string
        console_logging('info', f"Building connection string to upload monitoring script")
        # build SCP string and ensure it is placed in :~ home dir on ec2
        con_str = f'scp -o StrictHostKeyChecking=no -i {key_pair_name}.pem {monitoring_file} {ec2_user_name}@{instance_ip_addr}:~'

        console_logging('info', f"\033[1mConnection string: {con_str}\033[0m")

        console_logging('info', f"\033[1mUploading monitoring script to instance: {instance[0].id}\033[0m")

        # running script using subprocess.run  - check = True will raise an exception if the command fails while in the shell
        subprocess.run(con_str, shell=True, check=True)

    except Exception as error:
        console_logging('error', f"Error while building connection string to SCP to instance: {error}")

    console_logging('info', f"Running monitoring script on instance: {instance[0].id}")

    try:
        # now we need to allow the script to be executable and run it on the instance
        console_logging('info', f"Executing {monitoring_file} on instance: {instance[0].id}")
        
        # chmod the script to make it executable and run it with ./
        con_str = f'ssh -i {key_pair_name}.pem {ec2_user_name}@{instance_ip_addr} "chmod +x {monitoring_file} && ./{monitoring_file}"'

        console_logging('info', f"\033[1mConnection string: {con_str}\033[0m")

        # running script using subprocess.run  - check = True will raise an exception if the command fails while in the shell
        subprocess.run(con_str, shell=True, check=True)

    except Exception as error:
        console_logging('error', f"Error while running monitoring script on instance: {error}")
        
    pass


def test_ec2_website():
    # Test if the EC2 web server is active and reachable - 
    # Doing this before the monitoring script run to ensure web server will be displayed as running and no errors encountered 

    console_logging('info', f"Testing EC2 website: {instance_ip_addr}")
    sleep(10) # sleep for 10 seconds to allow the web server to try startup
    atmp_count = 0

    # give the web server 5 attempts to start up - this equates to 25 seconds 
    while atmp_count < 5:
        try:
            rsp = requests.get(f"http://{instance_ip_addr}", timeout=5)  # Timeout prevents hanging
            if rsp.status_code == 200:
                console_logging('info', "EC2 website is active and reachable")
                break
            else:
                console_logging('info', f"EC2 website is not active - Status: {rsp.status_code} - Retrying in 5 seconds")
        except Exception as e:
            console_logging('info', f"Error while trying to reach EC2 website http://{instance_ip_addr}- Retrying in 5 seconds")
        atmp_count += 1
        sleep(5)
    else:
        console_logging('error', "EC2 website is not active after 5 attempts")

        
    

# Main function to call the above functions 

def main():
    get_ipt_args()
    print()
    get_image()
    print()
    ec2_url_name = create_ec2_instance()
    print()
    create_ami()
    print()
    create_s3_bucket()
    print()
    make_s3_static() # call make static function to make the bucket static host
    print()
    s3_url_name = upload_to_s3()
    print()
    write_to_file(ec2_url_name , s3_url_name)
    print()
    test_ec2_website()
    print()
    upload_run_monitoring()
    print()
    if cleanup:
        cleanup_resources()
    print()
    for job in cleanup_jobs:
        console_logging('info', f"Status of removal post cleanup job: {job} - {'Success' if cleanup_jobs[job] else 'Failed'}")
    print()
    pass






if __name__ == '__main__':
    # clear the console
    subprocess.run('clear', shell=True)
    console_logging('info', "------------------------------")
    console_logging('info', "\033[1mACS Assignment 1 - Peter Walsh - Script Start\033[0m")
    main()
    console_logging('info', "\033[1mACS Assignment 1 - Peter Walsh - Script End\033[0m")
    console_logging('info', "------------------------------")



# Misc References
# https://www.kodeclik.com/how-to-bold-text-in-python/