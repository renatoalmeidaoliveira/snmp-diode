from enum import Enum
from typing import Tuple

from easysnmp import Session
import netaddr
from snmp_diode.models import Interface, Device
from snmp_diode.sysobjectid import manufacturers


class SNMPVersion(int, Enum):
    V2C = 2
    V3 = 3


class SNMPAUTH(str, Enum):
    AuthPriv = "authPriv"
    AuthNoPriv = "authNoPriv"


class OID(str, Enum):
    DEVICE_NAME = "iso.3.6.1.2.1.1.5.0"
    SYS_ID = "iso.3.6.1.2.1.1.2.0"
    LOCATION = "1.3.6.1.2.1.1.6.0"
    IF_NAME = "iso.3.6.1.2.1.2.2.1.2"
    IF_MAC = "1.3.6.1.2.1.2.2.1.6"
    IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"
    IF_ADDRESS = "iso.3.6.1.2.1.4.20.1.2"
    DESCRIPTION = "iso.3.6.1.2.1.31.1.1.1.18"
    ADDRESSES = "iso.3.6.1.2.1.4.20.1.1"
    ADDRESS_MASK = "iso.3.6.1.2.1.4.20.1.3"


def get_session_data(address: str, snmp_data: dict) -> dict:
    session_data = {
        "hostname": address,
        "use_sprint_value": True,
        "version": snmp_data.get("version"),
    }
    if snmp_data.get("version") == SNMPVersion.V2C:
        session_data["community"] = snmp_data.get("version_data").get("community")

    elif snmp_data.get("version") == SNMPVersion.V3:
        session_data["security_level"] = snmp_data.get("version_data").get("level")
        session_data["security_username"] = snmp_data.get("version_data").get("username")

        if snmp_data.get("version_data").get("level") == SNMPAUTH.AuthNoPriv:
            session_data["auth_protocol"] = snmp_data.get("version_data").get("auth_protocol")
            session_data["auth_password"] = snmp_data.get("version_data").get("auth")

        elif snmp_data.get("version_data").get("level") == SNMPAUTH.AuthPriv:
            session_data["auth_protocol"] = snmp_data.get("version_data").get("auth_protocol")
            session_data["auth_password"] = snmp_data.get("version_data").get("auth")
            session_data["privacy_protocol"] = snmp_data.get("version_data").get("privacy_protocol")
            session_data["privacy_password"] = snmp_data.get("version_data").get("privacy")

    return session_data


def get_device_data(address, snmp_data, role=None, site=None) -> Device:
    session_data: dict = get_session_data(address=address, snmp_data=snmp_data)
    
    session: Session = Session(**session_data)

    device_name_oid = session.get(OID.DEVICE_NAME)
    sys_id_oid = session.get(OID.SYS_ID)
    location_oid = session.get(OID.LOCATION)

    manufacturer, device_type = get_device_model(sys_oid=sys_id_oid.value)

    interfaces: list[Interface] = process_interfaces(session=session)

    return Device(
        name=device_name_oid.value.replace('"', ""),
        manufacturer=manufacturer,
        device_type=device_type,
        site=location_oid.value.replace('"', "") if site else site,
        interfaces=interfaces,
        role=role
    )


def process_interfaces(session: Session) -> list[Interface]:

    interfaces = {}
    for item in session.walk(OID.IF_NAME):
        iface_name = item.value
        interface_id = item.oid.split(".")[-1]
        interfaces[interface_id] = {"index": interface_id, "name": iface_name}

    for item in session.walk(OID.IF_MAC):
        interface_id = item.oid.split(".")[-1]
        interfaces[interface_id]["mac"] = item.value.replace('"', "")[:-1].replace(
            " ", ":"
        )

    for item in session.walk(OID.IF_ADMIN_STATUS):
        interface_id = item.oid.split(".")[-1]
        enabled = item.value == "1"

        interfaces[interface_id]["enabled"] = enabled

    addresses: dict = {}
    for item in session.walk(OID.ADDRESSES):
        addresses[item.value] = {"address": item.value}

    for item in session.walk(OID.IF_ADDRESS):
        address = item.oid.replace(f"{OID.IF_ADDRESS}.", "")
        if address in addresses:
            addresses[address]["if_oid"] = item.value

    for item in session.walk(OID.ADDRESS_MASK):
        address = item.oid.replace(f"{OID.ADDRESS_MASK}.", "")
        if address in addresses:
            addresses[address]["netmask"] = item.value

    for address in addresses:
        if addresses[address]["if_oid"] in interfaces:
            ip_net = netaddr.IPNetwork(
                    f'{addresses[address]["address"]}/{addresses[address]["netmask"]}'
                )
            interfaces[addresses[address]["if_oid"]]["address"] = f"{ip_net.ip}/{ip_net.prefixlen}"

    for item in session.walk(OID.DESCRIPTION):
        interface_id = item.oid.replace(f"{OID.DESCRIPTION}.", "")
        if interface_id in interfaces:
            interfaces[interface_id]["description"] = item.value.replace('"', "")

    return [
        Interface(
            name=entry.get("name").replace('"', ""),
            mac_address=entry.get("mac"),
            address=entry.get("address", None),
            description=entry.get("description", ""),
            enabled=entry.get("enabled"),
        )
        for entry in interfaces
    ]


def get_device_model(sys_oid: str) -> Tuple[str, str]:
    manufacturer: str = "unknown"
    device_type: str = "unknown"
    sys_oid_list: list[str] = sys_oid.split(".")

    if len(sys_oid_list) <= 6:
        return manufacturer, device_type

    manufacturer_id: int = int(sys_oid_list[6])

    if manufacturer_id in manufacturers:
        manufacturer = manufacturers[manufacturer_id]["name"]
        model_id = int(sys_oid_list[-1])

        if model_id in manufacturers[manufacturer_id]["products"]:
            device_type = manufacturers[manufacturer_id]["products"][model_id]

    return manufacturer, device_type
