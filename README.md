# Automated Cloud Services - Assessment 1

**Author:** Peter Walsh  
**Student ID:** 20098070  
**Course:** Year 4 Automation Engineering  

## Overview
This repository contains the code for **Assessment 1** of Automated Cloud Services. The script executes from start to finish and completes the following core tasks:

## Core Functionality
1. **Launch an EC2 Instance**  
2. **Instance Configuration (During Launch)**
   - Security Group setup  
   - Correct Key Pair assignment  
   - Availability Zone: `us-east-1`  
   - Instance Type: `t2.micro`  
3. **User Data Execution**
   - Applies patches  
   - Configures a web server  
   - Displays metadata from the instance  
4. **AMI Creation**  
5. **S3 Bucket Setup for Static Web Hosting**
   - Downloads and uploads an image from **SETU ACS Resources**  
   - Uploads an `index.html` file to display the image  
6. **TXT File Creation**
   - Provides links to both generated URLs  
7. **Monitoring Script Deployment**
   - `monitoring.sh` is copied to the instance using SCP  

## Non-Functional Enhancements
1. **Error Handling**  
   - `try-except` blocks implemented to manage failures  
2. **Logging**  
   - Logs critical events to a file  
   - Key points logged to the console  
3. **Code Documentation**
   - Inline comments (`#`) explaining code flow and purpose  
   - Additional explanations within the script  

## Additional Functionality (TBD)
Further enhancements will be added to improve the overall functionality of the script.
