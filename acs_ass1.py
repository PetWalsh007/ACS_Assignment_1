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
created_ami_name = tag_name + '_AMI'

##---------##


def create_ec2_instance():
    console_logging('info', f"Creating EC2 instance with tag name: {tag_name}")
    global instance_ip_addr
    global instance

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
    
    instance[0].wait_until_running() # wait until running to obtain ip address
    instance[0].reload() # Reload to get new info
    instance_ip_addr = instance[0].public_ip_address
    console_logging('info', f"Instance ID: {instance[0].id}")
    console_logging('info', f"Instance IP Address: {instance_ip_addr}")
    console_logging('info', f"Instance State: {instance[0].state['Name']}")
    console_logging('info', f"Instance is now available at http://{instance_ip_addr}")
    pass



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
    console_logging('info', f"Creating S3 bucket: {bucket_name_s3}")
    try:
        response = s3.create_bucket(Bucket=bucket_name_s3)
        console_logging('info', f"{response}")
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
    console_logging('info', f"Making {bucket_name_s3} a static website host")
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

        

    # Avoid redownlaoding the same image if it already exists in the directory - To be removed in final version
    if img_file_name in os.listdir():
        print(f"Image already exists in directory")
        return
    else:
        with open(img_file_name, "wb") as f:
            f.write(img_resource.content)

    pass


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

    
    console_logging('info', f"Uploading index.html to {bucket_name_s3}")
    html_index_data = get_html_data() # calls the get_html_data function to get the html data
    try:
        s3_client.put_object(Bucket=bucket_name_s3, Key='index.html', Body=html_index_data, ContentType='text/html') # uploads the index.html file to the bucket and set the content type to html
        console_logging('info', f"index.html uploaded to {bucket_name_s3}")
    except Exception as error:
        console_logging('error', f"Error while uploading index.html: {error}")

    console_logging('info', f"Website Available at http://{bucket_name_s3}.s3-website-us-east-1.amazonaws.com")


    pass



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
    sys.argv[1] = sys.argv[1].upper() # convert to uppercase to avoid case sensitivity
    if len(sys.argv) > 2:
        if sys.argv[1] == 'TRUE':
            cleanup = True
            console_logging('info', "Cleanup flag detected. Script will remove all resources after script completion")
            wait_time = int(sys.argv[2])
            console_logging('info', f"Wait time set to {wait_time} seconds post script completion")
        if sys.argv[1] == 'FALSE':
            console_logging('info', "No cleanup flag detected. Script will not remove resources after script completion")
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'TRUE':
            cleanup = True
            console_logging('info', "Cleanup flag detected. Script will remove all resources after script completion")
            wait_time = 30 # defualt wait time 
            console_logging('info', f"Wait time set to {wait_time} seconds post script completion")
    else:
        console_logging('info', "No cleanup flag detected. Script will not remove resources after script completion")




def cleanup_resources():
    # Cleanup function to remove all resources created during the script execution 
    # Note - flag here is set to false to avoid the program error function from being called recursively
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
    except Exception as error:
        console_logging('error', f"Error while deleting bucket: {error}", False)

    # Terminate EC2 instance
    console_logging('info', f"Terminating instance: {instance[0].id}")
    try:
        instance[0].terminate()
        console_logging('info', f"Terminated instance: {instance[0].id}")
    except Exception as error:
        console_logging('error', f"Error while terminating instance: {error}", False)
    
    console_logging('info', "Cleanup complete")
    pass


def program_error():
    cleanup_resources()
    console_logging('error', "Starting Exit of Program due to error in script", False)
    sys.exit(1)
    pass

# Main function to call the above functions 

def main():
    get_ipt_args()
    get_image()
    create_ec2_instance()
    create_ami()
    create_s3_bucket()
    make_s3_static() # call make static function to make the bucket static host
    upload_to_s3()

    if cleanup:
        cleanup_resources()
    
    pass







if __name__ == '__main__':
    
    console_logging('info', "------------------------------")
    console_logging('info', "ACS Assignment 1 - Peter Walsh - Script Start")
    main()
    console_logging('info', "ACS Assignment 1 - Peter Walsh - Script End")
    console_logging('info', "------------------------------")

