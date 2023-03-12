import boto3
region = 'us-east-2'
instances = ['i-07f66f8c594161e6b']


# lambda handler for stopping the instance
def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name=region)
    ec2.stop_instances(InstanceIds=instances)
    print('stopped your instances: ' + str(instances))
    # return 'stopped your instances: ' + str(instances)


# lambda handler for starting the instance
def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name=region)
    ec2.start_instances(InstanceIds=instances)
    print('started your instances: ' + str(instances))
