from botocore.exceptions import ClientError

from utils import *

import boto3

# Let's use Amazon S3
client = boto3.client('ec2')

DryRun = False
MaxInterfaces = 8
MaxIpsPerInterface = 30

InstanceId = 'i-06ea4a12f5622fbb5'
VpcId = 'vpc-0fa32ae9050503bf3'
SecurityGroupId = 'sg-06ea256f9f1be1c66'


def get_interfaces(instance_id):
    instances = client.describe_instances(Filters=[
        {
            'Name': 'instance-id',
            'Values': [instance_id]
        }
    ])

    instance = instances['Reservations'][0]['Instances'][0]

    return instance['NetworkInterfaces']


# Creates an elastic IP for any private IP addresses that do not currently have a public IP
def allocate_and_assign_address(instance_id):
    interfaces = get_interfaces(instance_id)

    for interface in interfaces:
        for private_ip in interface['PrivateIpAddresses']:
            if 'Association' not in private_ip:
                new_ip = client.allocate_address(Domain='vpc')
                client.associate_address(NetworkInterfaceId=interface['NetworkInterfaceId'],
                                         AllocationId=new_ip['AllocationId'],
                                         PrivateIpAddress=private_ip['PrivateIpAddress'])


# Allocates the max amount of private IPs to every interface on an instance
def allocate_private_ips(instance_id):
    interfaces = get_interfaces(instance_id)
    for interface in interfaces:
        numPrivIps = len(interface['PrivateIpAddresses'])
        if numPrivIps < MaxIpsPerInterface:
            response = client.assign_private_ip_addresses(
                AllowReassignment=False,
                NetworkInterfaceId=interface['NetworkInterfaceId'],
                SecondaryPrivateIpAddressCount=MaxIpsPerInterface - numPrivIps
            )


def check_subnet_exists(cidr):
    subnets = client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [VpcId]
            },
        ])
    for subnet in subnets['Subnets']:
        if subnet['CidrBlock'] == cidr:
            return True

    return False


def get_subnet_id(cidr):
    subnets = client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [VpcId]
            },
        ])
    for subnet in subnets['Subnets']:
        if subnet['CidrBlock'] == cidr:
            return subnet['SubnetId']

    return ''


def create_subnet(cidrBlock):
    subnet = client.create_subnet(CidrBlock=cidrBlock, VpcId=VpcId)
    subnet_id = subnet['Subnet']['SubnetId']
    client.associate_route_table(SubnetId=subnet_id, RouteTableId="rtb-0c9575e2f57fac800")
    print("Created subnet %s and associated route table", cidrBlock)
    return subnet_id


# Create up to max interfaces for the instance
def allocate_and_assign_interfaces(instance_id):
    num_interfaces = len(get_interfaces(instance_id))

    for i in range(num_interfaces, MaxInterfaces):
        cidr = '10.0.' + str(i) + '.0/24'
        subnet_id = get_subnet_id(cidr)
        if subnet_id == '':
            subnet_id = create_subnet(cidr)

        network_interface_res = client.create_network_interface(SubnetId=subnet_id, Groups=[SecurityGroupId])
        network_interface_id = network_interface_res['NetworkInterface']['NetworkInterfaceId']
        res = client.attach_network_interface(
            DeviceIndex=i,
            InstanceId=instance_id,
            NetworkInterfaceId=network_interface_id
        )

    return


def deallocate_unused_addresses():
    ips = client.describe_addresses()
    for ip in ips['Addresses']:
        try:
            res = client.release_address(AllocationId=ip['AllocationId'], DryRun=DryRun)
            print("Deallocated IP: %s" % ip['PublicIp'])

        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidIPAddress.InUse':
                print("Failed to deallocate IP: %s" % ip['PublicIp'])
                print(e.message)
            else:
                print("Unexpected error: %s" % e)

    return


def print_all_addresses():
    pretty_print(client.describe_addresses())
    return


def start_instance(instance_id):
    res = client.start_instances(InstanceIds=[instance_id])
    pretty_print(res)


def describe_instances():
    pretty_print(client.describe_instances())


#allocate_and_assign_interfaces(InstanceId)
#allocate_private_ips(InstanceId)
#allocate_and_assign_address(InstanceId)
#deallocate_unused_addresses()
