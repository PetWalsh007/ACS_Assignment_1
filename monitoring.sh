#!/usr/bin/bash
#
# Some basic monitoring functionality; Tested on Amazon Linux 2.
#
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)

echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "No of processes: $PROCESSES"
if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi

# Aditional funcionallity - 
echo " "
echo "Aditional Functionality - PWalsh - 20098070" 
echo " "
# Similar to above, using ps to get information about processes, such as memory and CPU usage - while sorting by memory usage before we pipe  head to get the top 4 processes.
# ps ran with -e for all processes and -o for user defined formatt
echo "Top Processes by CPU Usage:"
ps -eo %mem,%cpu,comm --sort=-%mem,-%cpu | head -n 4
UPTIME=$(uptime -p)
echo "System Uptime: $UPTIME"
# use netstat to get information about network connections but only show top 5 connections
echo "Top 5 Network Connections:"
netstat -tuln | head -n 5

