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

## Declarations and Global Variables ##

# ec2 initalisation 
ec2 = boto3.resource('ec2')

# s3 initalisation
s3 = boto3.client('s3')

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




def create_ec2_instance():

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
        UserData='''#!/bin/bash
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
                )
    
    instance[0].wait_until_running() # wait until running to obtain ip address
    instance[0].reload() # Reload to get new info
    instance_ip_addr = instance[0].public_ip_address
    print(f"Instance ID: {instance[0].id}")
    print(f"Instance IP Address: {instance_ip_addr}")
    print(f"Instance State: {instance[0].state}")
    pass


def create_ami():


    pass

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
def create_s3_bucket():

    try:
        response = s3.create_bucket(Bucket=bucket_name_s3)
        print (response)
    except Exception as error:
        print (error)



    pass

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-bucket-policies.html
def set_bucket_policy():

    # Create a bucket policy
    
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{bucket_name_s3}/*'
        }]
    }

    # Convert the policy from JSON dict to string
    bucket_policy = json.dumps(bucket_policy)
    try:
        s3.put_bucket_policy(Bucket=bucket_name_s3, Policy=bucket_policy)
        return True
    except Exception as error:
        print (error)
        return False


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-static-web-host.html
def make_s3_static():
    if set_bucket_policy():
        print("Bucket policy set successfully")
    
        website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'}}

        try:
            s3.put_bucket_website(Bucket=bucket_name_s3,
                            WebsiteConfiguration=website_configuration)
        except Exception as error:
            print (error)

    else:
            print("Error setting bucket policy")
        

    pass




   

def get_image():
    # https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions - request documentation for error handling

    try:
        img_resource = requests.get(img_dwl_url)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        

    # Avoid redownlaoding the same image if it already exists in the directory - To be removed in final version
    if img_file_name in os.listdir():
        print(f"Image already exists in directory")
        return
    else:
        with open(img_file_name, "wb") as f:
            f.write(img_resource.content)

    pass

def upload_to_s3():
    object = img_file_name
    file_type = '.' + object.split(".")[1]
    object = object.split(".")[0] + '_pwalsh' + file_type


    try:
        response = s3.upload_file(img_file_name, bucket_name_s3, object)
        print(response)
    except Exception as error:
        print(error)


    pass


# Main function to call the above functions 

def main():
    get_image()
    #create_ec2_instance()
    #create_ami()
    create_s3_bucket()
    make_s3_static()
    upload_to_s3()
    
    pass







if __name__ == '__main__':
    main()

