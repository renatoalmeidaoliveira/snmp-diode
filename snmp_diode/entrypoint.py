import argparse
import netaddr
import os
from netboxlabs.diode.sdk import DiodeClient
from snmp_diode import discover


parser = argparse.ArgumentParser(description="SNMP Discovery Tool for NetBoxLabs Diode")

snmpv3_levels = ["noAuthNoPriv", "authNoPriv", "authPriv"]
snmpv3_auth_protocols = ["MD5", "SHA"] 

parser.add_argument("-t", "--host", type=str, help="Target Host Address", required=False)
parser.add_argument("-n", "--network", type=str, help="Target Network Address", required=False)
parser.add_argument("-v", "--version", type=str, help="SNMP Version", required=True)
parser.add_argument("-c", "--community", type=str, help="SNMP Community String", required=False)
parser.add_argument("-u", "--username", type=str, help="SNMPv3 Username", required=False)
parser.add_argument("-a", "--auth", type=str, help="SNMPv3 Auth Password", required=False)
parser.add_argument("-A", "--auth_protocol", type=str, help="SNMPv3 Auth Protocol", required=False, choices=snmpv3_auth_protocols)
parser.add_argument("-x", "--privacy", type=str, help="SNMPv3 Privacy Password", required=False)
parser.add_argument("-X", "--privacy_protocol", type=str, help="SNMPv3 Privacy Protocol", required=False)
parser.add_argument("-l", "--level", type=str, help="SNMPv3 Security Level", required=False, choices=snmpv3_levels)
parser.add_argument("-d", "--diode", type=str, help="Diode Server", required=False)
parser.add_argument("-k", "--api_key", type=str, help="Diode API Key", required=False)
parser.add_argument( "--apply", action="store_true", default=False, help="Apply the changes to NetBox", required=False,)
parser.add_argument("-r", "--role" , type=str, help="Role of the device", required=False)
parser.add_argument("-s", "--site", type=str, help="Site of the device", required=False)
 

def main():
    args = parser.parse_args()
    versions = ["2", "v2c", "3"]
    if args.host is None and args.network is None:
        print("Please provide either a target IP address or a target network address")
        exit(1)
    if args.host is not None and args.network is not None:
        print(
            "Please provide either a target IP address or a target network address, not both"
        )
        exit(1)
    if args.version not in versions:
        print("Please provide a valid SNMP version, options are: 2, v2c, 3")
        exit(1)
    elif args.version == "2" or args.version == "v2c":
        version = 2
        if args.community is None:
            print("Please provide an SNMP community string")
            exit(1)
    elif args.version == "3":
        version = 3

    snmp_data = {
        "version": version,
    }
    if version == 2:
        snmp_data["version_data"] = {"community": args.community}
    elif version == 3:
        if args.level is None:
            print("Please provide an SNMPv3 security level")
            exit(1)
        if args.level == "authNoPriv":
            if args.username is None or args.auth is None or args.auth_protocol is None:
                print("Please provide a username, auth password, and auth protocol")
                exit(1)
            snmp_data["version_data"] = {
                "level": "authNoPriv",  # "authNoPriv", "authPriv", "noAuthNoPriv
                "username": args.username,
                "auth": args.auth,
                "auth_protocol": args.auth_protocol,
            }
        elif args.level == "authPriv":
            if (
                args.username is None
                or args.auth is None
                or args.auth_protocol is None
                or args.privacy is None
                or args.privacy_protocol is None
            ):
                print(
                    "Please provide a username, auth password, auth protocol, privacy password, and privacy protocol"
                )
                exit(1)
            snmp_data["version_data"] = {
                "level": "authPriv",  # "authNoPriv", "authPriv", "noAuthNoPriv
                "username": args.username,
                "auth": args.auth,
                "auth_protocol": args.auth_protocol,
                "privacy": args.privacy,
                "privacy_protocol": args.privacy_protocol,
            }
        elif args.level == "noAuthNoPriv":
            if args.username is None:
                print("Please provide a username")
                exit(1)
            snmp_data["version_data"] = {
                "level": "noAuthNoPriv",  # "authNoPriv", "authPriv", "noAuthNoPriv
                "username": args.username
                }
    
    api_key = args.api_key
    if args.apply:
        if args.diode is None:
            print("Please provide a Diode server, with the --diode or -d flag")
            exit(1)
        if args.api_key is None:
            api_key = os.getenv("DIODE_API_KEY")
        if api_key is None:
            print("Please provide a Diode API key, with the --api_key or -k flag, or set the DIODE_API_KEY environment variable")
            exit(1)

    entities = []
    discover_errors = {}
    if args.host:
        try:
            device_data = discover.gater_device_data(args.host, snmp_data, args.role, args.site)
            entities = entities + device_data.model_dump()
        except Exception as e:
            discover_errors[args.host] = str(e)

    if args.network:
        network = netaddr.IPNetwork(args.network)
        for address in network:
            try:
                device_data = discover.gater_device_data(str(address), snmp_data, args.role, args.site)
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
            api_key=api_key,
        ) as client:
            response = client.ingest(entities=entities)
            if response.errors:
                print(f"FAIL: response errors: {response.errors}")
            else:
                print("INFO: data ingested successfully")
