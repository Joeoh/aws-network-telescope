import csv

"""
	Generates a tshark query string that can be used to filter .pcap files for Mirai probes
	Input is from ip-addr.py
"""

with open('ips.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
    for row in reader:
        print "(tcp.seq == " + row[2] + " && ip.dst == " + row[1] + ") ||",
