import socket, struct
import boto3

"""
    Print the Public/Private IP Pairs and the public IP as a LONG.
    Used for mapping back to Mirai probes in .pcap files.

"""
client = boto3.client('ec2')

DryRun = False
MaxInterfaces = 8
MaxIpsPerInterface = 30

InstanceId = 'i-06ea4a12f5622fbb5'
VpcId = 'vpc-0fa32ae9050503bf3'
SecurityGroupId = 'sg-06ea256f9f1be1c66'


def print_address_pairs():
    address_res = client.describe_addresses()
    addresses = address_res['Addresses']
    for address in addresses:
        if address['InstanceId'] == InstanceId:
            print address['PublicIp'] + '\t' + address['PrivateIpAddress'] + '\t' + str(ip2long(address['PublicIp']))


def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]


