# Quick script to remove all S3 buckets and their contents to aid in testing and cleaning up AWS resources
import boto3

s3 = boto3.client('s3')
ec2 = boto3.resource('ec2')

def empty_s3_bucket(bucket_name):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for item in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=item['Key'])
        else:
            print(f"Bucket {bucket_name} is already empty")
    except Exception as error:
        print (error)

def delete_s3_bucket(bucket_name):
    try:
        s3.delete_bucket(Bucket=bucket_name)
    except Exception as error:
        print(error)


def main():
    buckets = s3.list_buckets()
    for bucket in buckets['Buckets']:
        empty_s3_bucket(bucket['Name'])
        delete_s3_bucket(bucket['Name'])

    
    insts = ec2.instances.all()
    for inst in insts:
        inst.terminate()
    


    pass

if __name__ == '__main__':
    main()
