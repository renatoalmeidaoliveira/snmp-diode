from pydantic import BaseModel, model_serializer
from typing import Optional
from netboxlabs.diode.sdk.ingester import (
    Device as DiodeDevice,
    Entity,
    Interface as DiodeInterface,
    IPAddress,
)


class Interface(BaseModel):
    name: str
    mac_address: str
    address: Optional[str] = None
    enabled: Optional[bool] = None


class Device(BaseModel):
    name: str
    device_type: str
    manufacturer: str
    platform: Optional[str] = None
    site: str
    interfaces: list[Interface]

    @model_serializer()
    def diode_serializaton(self) -> list:
        entity_list = []
        dev_entity = Entity(
            device=DiodeDevice(
                name=self.name,
                device_type=self.device_type,
                manufacturer=self.manufacturer,
                platform=self.platform,
                site=self.site,
            )
        )
        entity_list.append(dev_entity)
        for interface in self.interfaces:
            iface_entity = Entity(
                interface=DiodeInterface(
                    name=interface.name,
                    mac_address=interface.mac_address,
                    device=self.name,
                    site=self.site,
                    enabled=interface.enabled,
                )
            )
            entity_list.append(iface_entity)
            if interface.address:
                ip_entity = Entity(
                    ip_address=IPAddress(
                        address=interface.address,
                        interface=interface.name,
                        device=self.name,
                    )
                )
                entity_list.append(ip_entity)
        return entity_list
