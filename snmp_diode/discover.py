from easysnmp import Session
import netaddr
from snmp_diode import models
from snmp_diode.sysobjectid import manufacturers


def gater_device_data(address, snmp_data):
    session_data = {
        "hostname": address,
        "use_sprint_value": True,
        "version": snmp_data["version"],
    }
    if snmp_data["version"] == 2:
        session_data["community"] = snmp_data["version_data"]["community"]
    elif snmp_data["version"] == 3:
        session_data["security_level"] = snmp_data["version_data"]["level"]
        session_data["security_username"] = snmp_data["version_data"]["username"]
        if snmp_data["version_data"]["level"] == "authNoPriv":
            session_data["auth_protocol"] = snmp_data["version_data"]["auth_protocol"]
            session_data["auth_password"] = snmp_data["version_data"]["auth"]
        elif snmp_data["version_data"]["level"] == "authPriv":
            session_data["auth_protocol"] = snmp_data["version_data"]["auth_protocol"]
            session_data["auth_password"] = snmp_data["version_data"]["auth"]
            session_data["privacy_protocol"] = snmp_data["version_data"]["privacy_protocol"]
            session_data["privacy_password"] = snmp_data["version_data"]["privacy"]
        
    
    session = Session(**session_data)    

    device_name_oid = session.get("iso.3.6.1.2.1.1.5.0")
    sysid_oid = session.get("iso.3.6.1.2.1.1.2.0")
    location_oid = session.get("1.3.6.1.2.1.1.6.0")

    device_data = {"hostname": device_name_oid.value}
    manufacturer, device_type = get_device_model(sysid_oid.value)

    interfaces = process_interfaces(session)

    device_data = {
        "name": device_name_oid.value.replace('"', ""),
        "manufacturer": manufacturer,
        "device_type": device_type,
        "site": location_oid.value.replace('"', ""),
        "interfaces": interfaces,
    }
    return models.Device(**device_data)


def process_interfaces(session):
    if_name = session.walk("iso.3.6.1.2.1.2.2.1.2")

    interfaces = {}
    for item in if_name:
        iface_name = item.value
        interface_id = item.oid.split(".")[-1]
        interfaces[interface_id] = {"index": interface_id, "name": iface_name}

    if_mac = session.walk("1.3.6.1.2.1.2.2.1.6")

    for item in if_mac:
        iface_name = item.value
        interface_id = item.oid.split(".")[-1]
        interfaces[interface_id]["mac"] = item.value.replace('"', "")[:-1].replace(
            " ", ":"
        )

    if_admin = session.walk("1.3.6.1.2.1.2.2.1.7")


    for item in if_admin:
        iface_name = item.value
        interface_id = item.oid.split(".")[-1]
        enabled = False
        if item.value == "1":
            enabled = True
        interfaces[interface_id]["enabled"] = enabled

    address_items = session.walk("iso.3.6.1.2.1.4.20.1.1")

    addresses = {}
    for item in address_items:
        addresses[item.value] = {"address": item.value}

    address_if_items = session.walk("iso.3.6.1.2.1.4.20.1.2")

    for item in address_if_items:
        address = item.oid.replace("iso.3.6.1.2.1.4.20.1.2.", "")
        if address in addresses:
            addresses[address]["if_oid"] = item.value

    address_mask_items = session.walk("iso.3.6.1.2.1.4.20.1.3")

    for item in address_mask_items:
        address = item.oid.replace("iso.3.6.1.2.1.4.20.1.3.", "")
        if address in addresses:
            addresses[address]["netmask"] = item.value

    for address in addresses:
        if addresses[address]["if_oid"] in interfaces:
            ipnet = netaddr.IPNetwork(
                    f'{addresses[address]["address"]}/{addresses[address]["netmask"]}'
                )
            interfaces[addresses[address]["if_oid"]]["address"] = f"{ipnet.ip}/{ipnet.prefixlen}"

    description_items = session.walk("iso.3.6.1.2.1.31.1.1.1.18")
    

    for item in description_items:
        interface_id = item.oid.replace("iso.3.6.1.2.1.31.1.1.1.18.", "")
        if interface_id in interfaces:
            interfaces[interface_id]["description"] = item.value.replace('"', "")

    output = []
    for interface in interfaces:
        iface_data = {
            "name": interfaces[interface]["name"].replace('"', ""),
            "mac_address": interfaces[interface]["mac"],
            "enabled": interfaces[interface]["enabled"],
        }
        if "description" in interfaces[interface]:
            iface_data["description"] = interfaces[interface]["description"]
        if "address" in interfaces[interface]:
            iface_data["address"] = interfaces[interface]["address"]

        output.append(models.Interface(**iface_data))
    return output


def get_device_model(sysoid):
    manufacturer = "unknow"
    device_type = "unknow"
    sysoid_list = sysoid.split(".")
    if len(sysoid_list) > 6:
        man_id = int(sysoid_list[6])
        if man_id in manufacturers:
            manufacturer = manufacturers[man_id]["name"]
            model_id = int(sysoid_list[-1])
            if model_id in manufacturers[man_id]["products"]:
                device_type = manufacturers[man_id]["products"][model_id]
    return (manufacturer, device_type)
