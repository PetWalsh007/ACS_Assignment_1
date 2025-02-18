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






def create_ec2_instance():
    pass


def create_s3_bucket():
    pass

def get_image():
    
    img = requests.get("https://setuacsresources.s3-eu-west-1.amazonaws.com/image.jpeg")
    
    with open("image_SETU_ACS.jpeg", "wb") as f:
        f.write(img.content)

    pass



# Main function to call the above functions 

def main():
    create_ec2_instance()
    create_s3_bucket()
    get_image()
    pass







if __name__ == '__main__':
    main()

