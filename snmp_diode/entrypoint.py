import argparse
from snmp_diode import discover

parser = argparse.ArgumentParser(description='SNMP Discovery Tool for NetBoxLabs Diode') 

parser.add_argument('-a', '--addres', type=str, help='Target IP Address', required=False)
parser.add_argument('-n', '--network', type=str, help='Target Network Address', required=False)
parser.add_argument('-c', '--community', type=str, help='SNMP Community String', required=True)
parser.add_argument('-v', '--version', type=str, help='SNMP Version', required=True)
# parser.add_argument('-d', '--diode', type=str, help='Diode Server', required=True)
parser.add_argument('--apply', default=False, type=bool, help='Apply data to Diode Server')




def main():
    args = parser.parse_args()
    versions = ["2", "v2c", "3"]
    if args.addres is None and args.network is None:
        print("Please provide either a target IP address or a target network address")
        exit(1)

    if args.version not in versions:
        print("Please provide a valid SNMP version, options are: 2, v2c, 3")
        exit(1)
    
    elif args.version == "2" or args.version == "v2c":
        version = 2
    elif args.version == "3":
        version = 3
    snmp_data = {
        "version": version,
        "community": args.community,
    }
    if args.addres:
        device_data = discover.gater_device_data(args.addres, snmp_data)
        print(device_data.model_dump())

        
    