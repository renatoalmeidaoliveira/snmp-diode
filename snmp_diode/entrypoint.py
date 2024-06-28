import argparse
from snmp_diode import discover
import netaddr
from netboxlabs.diode.sdk import DiodeClient

parser = argparse.ArgumentParser(description="SNMP Discovery Tool for NetBoxLabs Diode")

parser.add_argument("-a", "--address", type=str, help="Target IP Address", required=False)
parser.add_argument("-n", "--network", type=str, help="Target Network Address", required=False)
parser.add_argument("-c", "--community", type=str, help="SNMP Community String", required=True)
parser.add_argument("-v", "--version", type=str, help="SNMP Version", required=True)
parser.add_argument("-d", "--diode", type=str, help="Diode Server", required=False)
parser.add_argument("-k", "--api_key", type=str, help="Diode API Key", required=False)
parser.add_argument( "--apply", default=False, type=bool, help="Apply the changes to NetBox", required=False,)


def main():
    args = parser.parse_args()
    versions = ["2", "v2c", "3"]
    if args.address is None and args.network is None:
        print("Please provide either a target IP address or a target network address")
        exit(1)
    if args.address is not None and args.network is not None:
        print(
            "Please provide either a target IP address or a target network address, not both"
        )
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
    if args.apply and (args.diode is None):
        print("Please provide a Diode server and API key")
        exit(1)

    entities = []
    discover_errors = {}
    if args.address:
        try:
            device_data = discover.gater_device_data(args.address, snmp_data)
            entities = entities + device_data.model_dump()
        except Exception as e:
            discover_errors[args.address] = str(e)

    if args.network:
        network = netaddr.IPNetwork(args.network)
        for address in network:
            try:
                device_data = discover.gater_device_data(str(address), snmp_data)
                entities = entities + device_data.model_dump()
            except Exception as e:
                discover_errors[address] = str(e)

    if discover_errors:
        print("ERROR: The following errors were encountered during discovery:")
        for address, error in discover_errors.items():
            print(f"ERROR: {address} - {error}")

    if not args.apply:
        print(entities)
    else:
        with DiodeClient(
            target=args.diode,
            app_name="snmp-diode",
            app_version="0.0.1",
            api_key=args.api_key,
        ) as client:
            response = client.ingest(entities=entities)
            if response.errors:
                print(f"FAIL: response errors: {response.errors}")
            else:
                print("INFO: data ingested successfully")
