from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory

import logging
from datetime import datetime

from . import NukiEntity, NukiBridge
from .constants import DOMAIN
from .states import DoorSensorStates, LockStates, DoorSecurityStates

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    coordinator = entry.runtime_data

    if coordinator.api.can_bridge():
        entities.append(BridgeWifiVersion(coordinator))
        entities.append(BridgeVersion(coordinator))
    for dev_id in coordinator.data.get("devices", {}):
        entities.append(LockState(coordinator, dev_id))
        if coordinator.api.can_bridge():
            entities.append(RSSI(coordinator, dev_id))
        entities.append(LockVersion(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "batteryChargeState"):
            entities.append(Battery(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "doorsensorStateName"):
            entities.append(DoorSensorState(coordinator, dev_id))
            entities.append(DoorSecurityState(coordinator, dev_id))
        if coordinator.info_field(dev_id, None, "web_last_update"):
            entities.append(WebLastUpdate(coordinator, dev_id))
        if coordinator.info_field(dev_id, None, "web_last_log"):
            entities.append(WebLastLog(coordinator, dev_id))
        if coordinator.info_field(dev_id, None, "web_last_lock_unlock_log"):
            entities.append(WebLastLockUnlockLog(coordinator, dev_id))
        
    async_add_entities(entities)
    return True


class Battery(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "battery")
        self.set_name("Battery")
        self._attr_device_class = "battery"
        self._attr_state_class = "measurement"

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_value(self):
        return self.last_state.get("batteryChargeState", 0)

    @property
    def state(self):
        return self.native_value

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class LockState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "state")
        self.set_name("State")
        self._attr_icon = "mdi:door"

    @property
    def state(self):
        return self.last_state.get("stateName")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class RSSI(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "rssi")
        self.set_name("RSSI")
        self._attr_device_class = "signal_strength"
        self._attr_state_class = "measurement"

    @property
    def native_unit_of_measurement(self):
        return "dBm"

    @property
    def native_value(self):
        return self.data.get("bridge_info", {}).get("rssi")

    @property
    def state(self):
        return self.native_value

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class DoorSensorState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "door_state")
        self.set_name("Door State")
        self._attr_icon = "mdi:door"

    @property
    def state(self):
        return self.last_state.get("doorsensorStateName")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class DoorSecurityState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "door_security_state")
        self.set_name("Door Security State")
        self._attr_icon = "mdi:door-closed-lock"

    @property
    def icon(self):

        state = self.get_state()

        if state == DoorSecurityStates.CLOSED_AND_LOCKED:
            return "mdi:door-closed-lock"
        elif state == DoorSecurityStates.CLOSED_AND_UNLOCKED:
            return "mdi:door-closed"
        return "mdi:door-open"

    @property
    def state(self):
        return str(self.get_state())

    def get_state(self) -> DoorSecurityStates:
        lock_state = LockStates(self.last_state.get("state", LockStates.UNDEFINED.value))
        door_sensor_state = DoorSensorStates(
            self.last_state.get("doorsensorState", DoorSensorStates.UNKNOWN.value))

        if lock_state == LockStates.LOCKED and door_sensor_state == DoorSensorStates.DOOR_CLOSED:
            return DoorSecurityStates.CLOSED_AND_LOCKED
        elif door_sensor_state == DoorSensorStates.DOOR_CLOSED:
            return DoorSecurityStates.CLOSED_AND_UNLOCKED
        return DoorSecurityStates.OPEN


class BridgeWifiVersion(NukiBridge, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("wifi_version")
        self.set_name("WiFi Firmware Version")

    @property
    def state(self):
        versions = self.data.get("versions", {})
        return versions.get("wifiFirmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class BridgeVersion(NukiBridge, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("version")
        self.set_name("Firmware Version")

    @property
    def state(self):
        versions = self.data.get("versions", {})
        return versions.get("firmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class LockVersion(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "version")
        self.set_name("Firmware Version")

    @property
    def state(self):
        return self.data.get("firmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

class WebLastUpdate(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "web_last_update")
        self.set_name("Web Last Update")
        self._attr_icon = "mdi:history"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def state(self):
        return self.coordinator.info_field(self.device_id, "Unknown", "web_last_update")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

class WebLastLog(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "web_last_log")
        self.set_name("Web Last Log")
        self._attr_icon = "mdi:history"

    @property
    def state(self):
        return self.coordinator.info_field(self.device_id, "Unknown", "web_last_log", "action")

    @property
    def extra_state_attributes(self):
        timestamp = self.coordinator.info_field(self.device_id, None, "web_last_log", "timestamp")
        name = self.coordinator.info_field(self.device_id, "unknown", "web_last_log", "name")
        device_type = self.coordinator.info_field(self.device_id, "unknown", "web_last_log", "device_type")
        trigger = self.coordinator.info_field(self.device_id, "unknown", "web_last_log", "trigger")
        state = self.coordinator.info_field(self.device_id, "unknown", "web_last_log", "state")
        source = self.coordinator.info_field(self.device_id, "unknown", "web_last_log", "source")
        return {
            "timestamp": datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None,
            "name": name,
            "device_type": device_type,
            "trigger": trigger,
            "state": state,
            "source": source,
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

class WebLastLockUnlockLog(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "web_last_lock_unlock_log")
        self.set_name("Web Last Lock Unlock Log")
        self._attr_icon = "mdi:account-lock-open"

    @property
    def state(self):
        return self.coordinator.info_field(self.device_id, "Unknown", "web_last_lock_unlock_log", "action")

    @property
    def extra_state_attributes(self):
        timestamp = self.coordinator.info_field(self.device_id, None, "web_last_lock_unlock_log", "timestamp")
        name = self.coordinator.info_field(self.device_id, "unknown", "web_last_lock_unlock_log", "name")
        trigger = self.coordinator.info_field(self.device_id, "unknown", "web_last_lock_unlock_log", "trigger")
        state = self.coordinator.info_field(self.device_id, "unknown", "web_last_lock_unlock_log", "state")
        source = self.coordinator.info_field(self.device_id, "unknown", "web_last_lock_unlock_log", "source")
        return {
            "timestamp": datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None,
            "name": name,
            "trigger": trigger,
            "state": state,
            "source": source,
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC