# snmp-diode

snmp-diode is a Python tool designed to gather device data using SNMP  and push it to NetBoxLabs Diode. 

## Features

- snmp-diode collects the following data using snmp:

| OID | NetBox Mapping |
| --- | ---- |
| 1.3.6.1.2.1.1.5.0 | Device Name |
| 1.3.6.1.2.1.1.2.0 | Manufacturer and Device Type |
| 1.3.6.1.2.1.1.6.0 | Site |
| 1.3.6.1.2.1.2.2.1.2 | Interface Name |
| 1.3.6.1.2.1.31.1.1.1.18 | Interface Description |
| 1.3.6.1.2.1.2.2.1.6 | Interface Mac Address |
| 1.3.6.1.2.1.2.2.1.7 | Interface Enabled Status |
| 1.3.6.1.2.1.4.20.1.2 | Interface IP Address |
| 1.3.6.1.2.1.4.20.1.3 | Interface Ip Address Mask |

## Installation

To install snmp-diode, follow these steps:

`$ pip install snmp-diode`

## Usage


```shell
usage: snmp-diode [-h] [-t HOST] [-n NETWORK] -v VERSION [-c COMMUNITY] [-u USERNAME] [-a AUTH] [-A {MD5,SHA}] [-x PRIVACY]
                  [-X PRIVACY_PROTOCOL] [-l {noAuthNoPriv,authNoPriv,authPriv}] [-d DIODE] [-k API_KEY] [--apply]

SNMP Discovery Tool for NetBoxLabs Diode

options:
  -h, --help            show this help message and exit
  -t HOST, --host HOST  Target Host Address
  -n NETWORK, --network NETWORK
                        Target Network Address
  -v VERSION, --version VERSION
                        SNMP Version
  -c COMMUNITY, --community COMMUNITY
                        SNMP Community String
  -u USERNAME, --username USERNAME
                        SNMPv3 Username
  -a AUTH, --auth AUTH  SNMPv3 Auth Password
  -A {MD5,SHA}, --auth_protocol {MD5,SHA}
                        SNMPv3 Auth Protocol
  -x PRIVACY, --privacy PRIVACY
                        SNMPv3 Privacy Password
  -X PRIVACY_PROTOCOL, --privacy_protocol PRIVACY_PROTOCOL
                        SNMPv3 Privacy Protocol
  -l {noAuthNoPriv,authNoPriv,authPriv}, --level {noAuthNoPriv,authNoPriv,authPriv}
                        SNMPv3 Security Level
  -d DIODE, --diode DIODE
                        Diode Server
  -k API_KEY, --api_key API_KEY
                        Diode API Key
  --apply               Apply the changes to NetBox

```

### Host mode

With -t flag snmp-diode discovers only the target host, usage sample:

```shell
$ export DIODE_API_KEY=1234567890098765432
$ snmp-diode -t 172.20.20.1 -v 2 -c public -d grpc://192.168.224.137:8081/diode --apply 
```
### Network mode

With -n flag snmp-diode discovers the target network (CIDR format, i.e. 10.0.0.0/24 ) including the network address and mask, usage sample:

```shell
$ export DIODE_API_KEY=1234567890098765432
$ snmp-diode -n 172.20.20.0/24 -v 2 -c public -d grpc://192.168.224.137:8081/diode --apply 
```

### Dry mode

Running snmp-diode without the --apply flag it gonna discover the target devices and print the Diode Entities.

```shell
$ snmp-diode -n 172.20.20.0/24 -v 2 -c public
```

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
