#!/usr/bin/python2

# Copyright 2010 Aerva, Inc
# Copyright 2010 Gavin Bisesi
# Copyright 2010 Mark Renouf
# Copyright 2012 s7mx1
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dbus
import enum
import socket
import ipaddr
try:
    import xbmc
except:
    import syslog
from binascii import unhexlify

DBUS_NAME="org.freedesktop.DBus"
DBUS_PROPS_NAME="org.freedesktop.DBus.Properties"

NM_NAME="org.freedesktop.NetworkManager"
NM_PATH="/org/freedesktop/NetworkManager"

NM_DEVICE="org.freedesktop.NetworkManager.Device"
NM_DEVICE_WIRED="org.freedesktop.NetworkManager.Device.Wired"
NM_DEVICE_WIRELESS="org.freedesktop.NetworkManager.Device.Wireless"
NM_DEVICE_CDMA="org.freedesktop.NetworkManager.Device.Cdma"
NM_CONN_ACTIVE="org.freedesktop.NetworkManager.Connection.Active"


NM_SETTINGS_NAME="org.freedesktop.NetworkManagerSettings"
NM_SETTINGS_PATH="/org/freedesktop/NetworkManagerSettings"
NM_SETTINGS_CONNECTION="org.freedesktop.NetworkManagerSettings.Connection"
try:
    settings=dbus.SystemBus().get_object(NM_NAME, NM_SETTINGS_PATH)
    settings.ListConnections(dbus_interface=NM_SETTINGS_NAME)
except:
    NM_SETTINGS_NAME="org.freedesktop.NetworkManager.Settings"
    NM_SETTINGS_PATH="/org/freedesktop/NetworkManager/Settings"
    NM_SETTINGS_CONNECTION="org.freedesktop.NetworkManager.Settings.Connection"

NM_ACCESSPOINT="org.freedesktop.NetworkManager.AccessPoint"

NM_IP4CONFIG="org.freedesktop.NetworkManager.IP4Config"

State = enum.new("State",
    # The NetworkManager daemon is in an unknown state.
    UNKNOWN = 0,
    # The NetworkManager daemon is asleep and all interfaces managed by it are inactive.
    ASLEEP = 1,
    # The NetworkManager daemon is connecting a device.
    # FIXME: What does this mean when one device is active and another is connecting?
    CONNECTING = 2,
    # The NetworkManager daemon is connected.
    CONNECTED = 3,
    # The NetworkManager daemon is disconnected.
    DISCONNECTED = 4
)

DeviceType = enum.new("DeviceType", UNKNOWN=0, ETHERNET=1, WIFI=2, GSM=3, CDMA=4)

DeviceState = enum.new("DeviceState",
    #The device is in an unknown state.
    UNKNOWN = 0,
    #The device is not managed by NetworkManager.
    UNMANAGED = 1,
    #The device cannot be used (carrier off, rfkill, etc).
    UNAVAILABLE = 2,
    #The device is not connected.
    DISCONNECTED = 3,
    #The device is preparing to connect.
    PREPARE = 4,
    #The device is being configured.
    CONFIG = 5,
    #The device is awaiting secrets necessary to continue connection.
    NEED_AUTH = 6,
    #The IP settings of the device are being requested and configured.
    IP_CONFIG = 7,
    #The device is active.
    ACTIVATED = 8,
    #The device is in a failure state following an attempt to activate it.
    FAILED = 9,
)

ActiveConnectionState = enum.new("ActiveConnectionState",
    #The active connection is in an unknown state.
    UNKNOWN = 0,
    #The connection is activating.
    ACTIVATING = 1,
    #The connection is activated.
    ACTIVATED = 2,
)

DeviceCap = enum.new("DeviceCap",
    NONE = 0,
    SUPPORTED = 1,
    CARRIER_DETECT = 2,
)

# NM_802_11_MODE
WifiMode = enum.new("WifiMode",
    #Mode is unknown.
    UNKNOWN = 0,
    #Uncoordinated network without central infrastructure.
    ADHOC = 1,
    #Coordinated network with one or more central controllers.
    INFRA = 2,
)

# NM_DEVICE_STATE_REASON
DeviceStateReason = enum.new("DeviceStateReason",
    #The reason for the device state change is unknown.
    UNKNOWN = 0,
    #The state change is normal.
    NONE = 1,
    #The device is now managed.
    NOW_MANAGED = 2,
    #The device is no longer managed.
    NOW_UNMANAGED = 3,
    #The device could not be readied for configuration.
    CONFIG_FAILED = 4,
    #IP configuration could not be reserved (no available address, timeout, etc).
    CONFIG_UNAVAILABLE = 5,
    #The IP configuration is no longer valid.
    CONFIG_EXPIRED = 6,
    #Secrets were required, but not provided.
    NO_SECRETS = 7,
    #The 802.1X supplicant disconnected from the access point or authentication server.
    SUPPLICANT_DISCONNECT = 8,
    #Configuration of the 802.1X supplicant failed.
    SUPPLICANT_CONFIG_FAILED = 9,
    #The 802.1X supplicant quit or failed unexpectedly.
    SUPPLICANT_FAILED = 10,
    #The 802.1X supplicant took too long to authenticate.
    SUPPLICANT_TIMEOUT = 11,
    #The PPP service failed to start within the allowed time.
    PPP_START_FAILED = 12,
    #The PPP service disconnected unexpectedly.
    PPP_DISCONNECT = 13,
    #The PPP service quit or failed unexpectedly.
    PPP_FAILED = 14,
    #The DHCP service failed to start within the allowed time.
    DHCP_START_FAILED = 15,
    #The DHCP service reported an unexpected error.
    DHCP_ERROR = 16,
    #The DHCP service quit or failed unexpectedly.
    DHCP_FAILED = 17,
    #The shared connection service failed to start.
    SHARED_START_FAILED = 18,
    #The shared connection service quit or failed unexpectedly.
    SHARED_FAILED = 19,
    #The AutoIP service failed to start.
    AUTOIP_START_FAILED = 20,
    #The AutoIP service reported an unexpected error.
    AUTOIP_ERROR = 21,
    #The AutoIP service quit or failed unexpectedly.
    AUTOIP_FAILED = 22,
    #Dialing failed because the line was busy.
    MODEM_BUSY = 23,
    #Dialing failed because there was no dial tone.
    MODEM_NO_DIAL_TONE = 24,
    #Dialing failed because there was carrier.
    MODEM_NO_CARRIER = 25,
    #Dialing timed out.
    MODEM_DIAL_TIMEOUT = 26,
    #Dialing failed.
    MODEM_DIAL_FAILED = 27,
    #Modem initialization failed.
    MODEM_INIT_FAILED = 28,
    #Failed to select the specified GSM APN.
    GSM_APN_FAILED = 29,
    #Not searching for networks.
    GSM_REGISTRATION_NOT_SEARCHING = 30,
    #Network registration was denied.
    GSM_REGISTRATION_DENIED = 31,
    #Network registration timed out.
    GSM_REGISTRATION_TIMEOUT = 32,
    #Failed to register with the requested GSM network.
    GSM_REGISTRATION_FAILED = 33,
    #PIN check failed.
    GSM_PIN_CHECK_FAILED = 34,
    #Necessary firmware for the device may be missing.
    FIRMWARE_MISSING = 35,
    #The device was removed.
    REMOVED = 36,
    #NetworkManager went to sleep.
    SLEEPING = 37,
    #The device's active connection was removed or disappeared.
    CONNECTION_REMOVED = 38,
    #A user or client requested the disconnection.
    USER_REQUESTED = 39,
    #The device's carrier/link changed.
    CARRIER = 40,
    #The device's existing connection was assumed.
    CONNECTION_ASSUMED = 41,
    #The 802.1x supplicant is now available.
    SUPPLICANT_AVAILABLE = 42,
)

def network_int_to_ip4addr(n):
    return str(ipaddr.IPAddress(socket.ntohl(n), version=4))

def ip4addr_to_network_int(addr):
    return socket.htonl(int(ipaddr.IPAddress(addr, version=4)))

def prefixlen_to_netmask(prefixlen):
    all_ones = (2**32) - 1
    netmask_int = all_ones ^ (all_ones >> prefixlen)
    return str(ipaddr.IPAddress(netmask_int))

def netmask_to_prefixlen(netmask):
    prefixlen=32
    ip_int = int(ipaddr.IPAddress(netmask))
    while prefixlen:
        if ip_int & 1 == 1:
            break
        ip_int >>= 1
        prefixlen -= 1

    return prefixlen

class Device(object):
    _NM_INTERFACE = NM_DEVICE

    def __new__(cls, bus, path):
        _subclasses = {
            DeviceType.ETHERNET: DeviceWired,
            DeviceType.WIFI: DeviceWireless,
            DeviceType.CDMA: DeviceCdma,
        }
        device = bus.get_object(NM_NAME, path)
        type = DeviceType.from_value(device.Get(NM_DEVICE, 'DeviceType'))
        try:
            cls = _subclasses[type]
        except KeyError:
            cls = Device

        return object.__new__(cls)

    def __init__(self, bus, object_path):
        self.bus = bus
        self.proxy = bus.get_object(NM_NAME, object_path)

    def __repr__(self):
        return "<Device: %s [%s]>" % (self.interface, self.hwaddress)

    def __str__(self):
        return self.interface

    def disconnect(self):
        self.proxy.Disconnect()

    def _proxy_get(self, target):
        return self.proxy.Get(self._NM_INTERFACE, target)

    @property
    def udi(self):
        return self._proxy_get("Udi")

    @property
    def interface(self):
        return self._proxy_get("Interface")

    @property
    def hwaddress(self):
        return None

    @property
    def driver(self):
        return self._proxy_get("Driver")

    @property
    def capabilities(self):
        caps = []
        value = self._proxy_get("Capabilities")
        if value & 0x01:
            caps.append(DeviceCap.SUPPORTED)
        if value & 0x02:
            caps.append(DeviceCap.CARRIER_DETECT)

        return caps

    @property
    def ipv4_address(self):
        return self.proxy.Get(NM_DEVICE, "Ip4Address")

    @property
    def state(self):
        return DeviceState.from_value(self._proxy_get("State"))

    @property
    def ip4config(self):
        return IP4Config(self.bus, self.proxy.Get(NM_DEVICE, "Ip4Config"))

    @property
    def dhcp4config(self):
        return None

    @property
    def ip6config(self):
        return None

    @property
    def managed(self):
        return self._proxy_get("Managed") == 1

    @property
    def type(self):
        return DeviceType.from_value(self._proxy_get("DeviceType"))

class DeviceWired(Device):
    _NM_INTERFACE = NM_DEVICE_WIRED

    def __init__(self, bus, object_path):
        Device.__init__(self, bus, object_path)

    @property
    def hwaddress(self):
        return self._proxy_get('HwAddress')

    @property
    def speed(self):
        return self._proxy_get('Speed')

    @property
    def carrier(self):
        return self._proxy_get('Carrier')

    @property
    def ip4config(self):
        return IP4Config(self.bus, self.proxy.Get(NM_DEVICE, "Ip4Config"))

    @property
    def ipv4_address(self):
        return self.proxy.Get(NM_DEVICE, "Ip4Address")

class DeviceWireless(Device):
    _NM_INTERFACE = NM_DEVICE_WIRELESS

    def __init__(self, bus, object_path):
        Device.__init__(self, bus, object_path)

    @property
    def access_points(self):
        return [AccessPoint(self.bus, path)
        for path in self.proxy.GetAccessPoints(dbus_interface=NM_DEVICE_WIRELESS)]

    @property
    def hwaddress(self):
        return self._proxy_get("HwAddress")

    @property
    def mode(self):
        return WifiMode.from_value(self._proxy_get("Mode"))

    @property
    def bitrate(self):
        return self._proxy_get("Bitrate")

    @property
    def active_access_point(self):
        return self._proxy_get("ActiveAccessPoint")

    @property
    def wireless_capabilities(self):
        return self._proxy_get("WirelessCapabilities")

class DeviceCdma(Device):
    _NM_INTERFACE = NM_DEVICE_CDMA

    def __init__(self, bus, object_path):
        Device.__init__(self, bus, object_path)

    @property
    def number(self):
        return self._proxy_get("Number")

    @property
    def username(self):
        return self._proxy_get("Username")

    @property
    def password(self):
        return self._proxy_get("Password")

class IP4Config(object):
    def __init__(self, bus, path):
        self.proxy = bus.get_object(NM_NAME, path)

    @property
    def addresses(self):
        return [
            [network_int_to_ip4addr(addr[0]),
             prefixlen_to_netmask(addr[1]),
             network_int_to_ip4addr(addr[2])]
            for addr in
                self.proxy.Get(NM_IP4CONFIG, "Addresses")]

    @property
    def name_servers(self):
        return [network_int_to_ip4addr(addr)
            for addr in
                self.proxy.Get(NM_IP4CONFIG, "Nameservers")]

    @property
    def wins_servers(self):
        return [network_int_to_ip4addr(addr)
            for addr in
                self.proxy.Get(NM_IP4CONFIG, "WinsServers")]

    @property
    def domains(self):
        return [str(value)
            for value in self.proxy.Get(NM_IP4CONFIG, "Domains")]

    @property
    def routes(self):
        return [
            [network_int_to_ip4addr(route[0]),
            prefixlen_to_netmask(route[1]),
            network_int_to_ip4addr(route[2]),
            route[3]]
                for route in
                    self.proxy.Get(NM_IP4CONFIG, "Routes")]

class AccessPoint(object):
    _NM_INTERFACE = NM_ACCESSPOINT

    def __init__(self, bus, path):
        self.proxy = bus.get_object(NM_NAME, path)

    def _proxy_get(self, target):
        return self.proxy.Get(self._NM_INTERFACE, target)

    @property
    def flags(self):
        return self._proxy_get("Flags")

    @property
    def wpaflags(self):
        return self._proxy_get("WpaFlags")

    @property
    def rsnflags(self):
        return self._proxy_get("RsnFlags")

    @property
    def ssid(self):
        return self._proxy_get("Ssid")

    @property
    def frequency(self):
        return self._proxy_get("Frequency")

    @property
    def hwaddress(self):
        return self._proxy_get("HwAddress")

    @property
    def mode(self):
        return self._proxy_get("Mode")

    @property
    def maxbitrate(self):
        return self._proxy_get("MaxBitrate")

    @property
    def strength(self):
        return self._proxy_get("Strength")


class NetworkManager(object):
    # Map of subclasses to return for different device types

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object(NM_NAME, NM_PATH)
        self.settings = self.bus.get_object(NM_NAME, NM_SETTINGS_PATH)

    def __repr__(self):
        return "<NetworkManager>"

    def sleep(self, sleep):
        pass

    def _proxy_get(self, target):
        return self.proxy.Get(self._NM_INTERFACE, target)

    def reload(self):
        self.proxy.Enable(dbus.Boolean(0))
        self.proxy.Enable(dbus.Boolean(1))

    @property
    def devices(self):
        """
        Returns a list of devices known to the system
        """
        # TODO: return dict keyed by dev
        return [Device(self.bus, path) for path in self.proxy.GetDevices()]

    @property
    def devices_map(self):
        """
        Returns a dict where the keys are device types and values are lists
        of devices of that type.
        """
        devices = {}

        for path in self.proxy.GetDevices():
            device = Device(self.bus, path)
            if not device.type in devices:
                devices[device.type] = [device]
            else:
                devices[device.type].append(device)

        return devices

    @property
    def connections(self):
        return [Connection(self.bus, path)
        for path in self.settings.ListConnections(dbus_interface=NM_SETTINGS_NAME)]

    @property
    def connections_map(self):
        """
        Returns a dict where the keys are uuids and the values are the
        corresponding connection objects
        """
        connections = {}

        for path in self.settings.ListConnections(dbus_interface=NM_SETTINGS_NAME):
            conn = Connection(self.bus, path)
            connections[str(conn.settings.uuid)] = conn

        return connections

    def get_connection(self, uuid):
        """
        Returns a single connection given a connection UUID, or None if no
        connection exists with that UUID
        """
        return self.connections_map.get(uuid)

    def get_connections_by_id(self, id):
        """
        Returns a list of connections that have the specified id, or None
        if no connections exist with that id
        """
        return filter(lambda con: con.settings.id == id, self.connections) or None

    @property
    def active_connections(self):
        return [ActiveConnection(self.bus, path)
            for path in self.proxy.Get(NM_SETTINGS_ACTIVE_CONNECTION, "Connection")]

    def add_connection(self, settings):
        self.settings.AddConnection(settings._settings, dbus_interface=NM_SETTINGS_NAME)

    def activate_connection(self, connection, device, service_name="org.freedesktop.NetworkManagerSystemSettings", specific_object="/"):
        self.proxy.ActivateConnection(service_name, connection.proxy, device.proxy, specific_object, dbus_interface=NM_NAME)

    def deactivate_connection(self, active_connection):
        self.proxy.DeactivateConnection(active_connection, dbus_interface=NM_NAME)

    @property
    def wireless_enabled(self):
        """Indicates if wireless is currently enabled or not."""
        return self.proxy.Get(NM_NAME, "WirelessEnabled",
            dbus_interface=DBUS_PROPS_NAME) != 0

    @wireless_enabled.setter
    def wireless_enabled(self, state):
        """Sets whether wireless should be enabled or not."""
        self.proxy.Set(NM_NAME, "WirelessEnabled", dbus.Boolean(state),
            dbus_interface=DBUS_PROPS_NAME)

    @property
    def wireless_hardware_enabled(self):
        """
        Indicates if the wireless hardware is currently
        enabled, i.e. the state of the RF kill switch.
        """
        return self.proxy.Get(NM_NAME, "WirelessHardwareEnabled",
            dbus_interface=DBUS_PROPS_NAME) != 0

    @property
    def state(self):
        """
        Describes the overall state of the daemon.
        """
        return State.from_value(self.proxy.Get(NM_NAME, "State"))

class ActiveConnection():
    _NM_INTERFACE = NM_CONN_ACTIVE

    def __init__(self, bus, path):
        self.bus = bus
        self.proxy = bus.get_object(NM_NAME, path)

    def __repr__(self):
        return "<ActiveConnection: %s>" % self.connection.settings.id

    def _proxy_get(self, target):
        return self.proxy.Get(self._NM_INTERFACE, target)

    @property
    def service_name(self):
        return self._proxy_get("ServiceName")

    @property
    def connection(self):
        path = self._proxy_get("Connection")
        return Connection(self.bus, path)

    @property
    def specific_object(self):
        return self._proxy_get("SpecificObject")

    @property
    def devices(self):
        return [Device(self.bus, path) for path in self._proxy_get("Devices")]

    @property
    def state(self):
        return ActiveConnectionState.from_value(
            self._proxy_get("State"))

    @property
    def default(self):
        return self._proxy_get("Default")

    @property
    def vpn(self):
        return self._proxy_get("Vpn")

class Connection():
    def __init__(self, bus, path):
        self.proxy = bus.get_object(NM_NAME, path);

    def __repr__(self):
        return "<Connection: \"%s\">" % self.settings.id

    @property
    def settings(self):
        """
        Returns this connections settings - a{sa{sv}} (String_String_Variant_Map_Map)
        The nested settings maps describing this object.
        """
        return Settings(self.proxy.GetSettings(dbus_interface=NM_SETTINGS_CONNECTION))

    def update(self, settings):
        """
        Update the connection to reflect the current values within the specified
        settings object (must be a subclass of Settings)
        """
        try:
            xbmc.log("updating settings")
            xbmc.log("settings._settings "+str(settings._settings))
        except:
            syslog.syslog("updating settings")
            syslog.syslog("settings._settings "+str(settings._settings))
        self.proxy.Update(settings._settings, dbus_interface=NM_SETTINGS_CONNECTION)

    def delete(self):
        """ Removes this connection """
        self.proxy.Delete(dbus_interface=NM_SETTINGS_CONNECTION)


class UnsupportedConnectionType(Exception):
    """ Encountered an unknown value within connection->type """

# FIXME: This seems smelly... replace with composition?
_default_settings_wired = dbus.Dictionary({
    'connection': dbus.Dictionary({
        'type': '802-3-ethernet',
    }),
    '802-3-ethernet': dbus.Dictionary({
        'auto-negotiate': True,
    }),
    'ipv4': dbus.Dictionary({
        'routes': dbus.Array([], signature='au'),
        'addresses': dbus.Array([], signature='au'),
        'dns': dbus.Array([],signature='u'),
        'dns-search': dbus.Array([],signature='s'),
        'dhcp-client-id': dbus.String(), 
        'method': 'auto',
    }),
    'ipv6': dbus.Dictionary({
        'routes': dbus.Array([], signature='(ayuayu)'),
        'addresses': dbus.Array([], signature='(ayu)'),
        'dns': dbus.Array([],signature='ay'),
        'dns-search': dbus.Array([],signature='s'),
        'dhcp-client-id': dbus.String(),
        'method': 'ignore',
    })
})

_default_settings_wireless = dbus.Dictionary({
    'connection': dbus.Dictionary({
        'type': '802-11-wireless',
    }),
    '802-11-wireless': dbus.Dictionary({}),
    'ipv4': dbus.Dictionary({
        'routes': dbus.Array([], signature='au'),
        'addresses': dbus.Array([], signature='au'),
        'dns': dbus.Array([],signature='u'),
        'method': 'auto',
    }),
    'ipv6': dbus.Dictionary({
        'routes': dbus.Array([], signature='(ayuayu)'),
        'addresses': dbus.Array([], signature='(ayu)'),
        'dns': dbus.Array([],signature='ay'),
        'method': 'ignore',
    })
})

_default_settings_cdma = dbus.Dictionary({
    'connection': dbus.Dictionary({
        'type': 'cdma',
    }),
    'cdma': dbus.Dictionary({
        'number': '#777',
    }),
    'ipv4': dbus.Dictionary({
        'routes': dbus.Array([], signature='au'),
        'addresses': dbus.Array([], signature='au'),
        'dns': dbus.Array([],signature='u'),
        'method': 'auto',
    }),
    'ppp': dbus.Dictionary({}),
    'serial': dbus.Dictionary({
        'baud': dbus.UInt32(115200L, variant_level=1)
    }),
})

def Settings(settings):
    # TODO: Refactor into a class like Device
    try:
        conn_type = settings['connection']['type']
    except KeyError:
        raise UnsupportedConnectionType("settings: connection.type is missing")

    if conn_type == "802-3-ethernet":
        settings = WiredSettings(settings)
        if settings.id is None:
            settings.id = 'Wired Connection'
    elif conn_type == "802-11-wireless":
        settings = WirelessSettings(settings)
        if settings.id is None:
            settings.id = 'Wireless Connection'
    elif conn_type == "cdma":
        settings = CdmaSettings(settings)
        if settings.id is None:
            settings.id = 'CDMA Connection'
    else:
        raise UnsupportedConnectionType("Unknown connection type: '%s'" % conn_type)

    return settings

class BaseSettings(object):

    _ALL_ONES = all_ones = (2**32) - 1

    def __init__(self, settings):
        self._settings = settings
        self.conn_type = settings['connection']['type']

    def __repr__(self):
        return "<Settings>"


    def _has_address(self):
        """
        Internal function

        Returns True if there is at least one address assigned
        within this connection. No addresses usually indicates
        autoconfiguration
        """
        if not 'ipv4' in self._settings: return False
        return len(self._settings['ipv4']['addresses']) > 0

    def _get_first_address(self):
        """
        Internal function

        Returns the first 'address' defined which is actually
        an (address, maskbits, gateway) triplet within an array.

        If an address is not defined, one is created, assigned and returned.

        Note: Does not support multiple addresses on a single connection.
        """
        addresses = []
        if 'ipv4' in self._settings:
            addresses = self._settings['ipv4']['addresses']

        if len(addresses) == 0:
            addresses = dbus.Array([dbus.Array([dbus.UInt32(0), dbus.UInt32(0), dbus.UInt32(0)], signature='u')], signature='au')
            if not 'ipv4' in self._settings:
                self._settings['ipv4'] = {}
            self._settings['ipv4']['addresses'] = addresses
        return addresses[0] # NOTE: only reports from first address!

    @property
    def id(self):
        """ The 'id' or name of the connection """
        return self._settings['connection']['id'] if 'id' in self._settings['connection'] else None

    @id.setter
    def id(self, value):
        self._settings['connection']['id'] = value

    @property
    def uuid(self):
        return self._settings['connection']['uuid'] if 'uuid' in self._settings['connection'] else None

    @uuid.setter
    def uuid(self, uuid):
        self._settings['connection']['uuid'] = str(uuid)

    @property
    def type(self):
        """ The connection type (usually indicates media standard) """
        return self._settings['connection']['type']

    @property
    def autoconnect(self):
        try:
            return self._settings['connection']['autoconnect']
        except KeyError:
            return False

    @autoconnect.setter
    def autoconnect(self, value):
        self._settings['connection']['autoconnect'] = value

    @property
    def timestamp(self):
        return self._settings['connection']['timestamp'] if 'timestamp' in self._settings else 0

    @property
    def mac_address(self):
        """ The mac address of the connection if only a specific adapter should be used """
        eth = self._settings[self.conn_type]
        if not 'mac-address' in eth: return None
        address = self._settings[self.conn_type]['mac-address']
        return ":".join([("%02X" % int(value)) for value in address])

    @mac_address.setter
    def mac_address(self, address):
        if address is None:
            del self._settings[self.conn_type]['mac-address']
        else:
            bytes = [unhexlify(v) for v in address.split(":")]
            self._settings[self.conn_type]['mac-address'] = dbus.Array(bytes, signature='y')

    @property
    def auto(self):
        """ Return True if this connection uses network autoconfiguration """
        if not self._has_address():
            return True
        return self._settings['ipv4']['method'] == 'auto'

    def set_auto(self):
        """ Configure this connection for network autoconfiguration """
        self._settings['ipv4'] = {
            'routes': dbus.Array([], signature='au'),
            'addresses': dbus.Array([], signature='au'),
            'dns': dbus.Array([], signature='u'),
            'dns-search': dbus.Array([],signature='s'),
            'dhcp-client-id': dbus.String(),
            'method': 'auto',}

    @property
    def address(self):
        """
        Returns the IPv4 address assigned to this connection in
        dotted-quad notation, or None if the connection has no
        statically assigned address information.
        """
        if not self._has_address():
            return None

        entry = self._get_first_address()
        return network_int_to_ip4addr(entry[0])


    @address.setter
    def address(self, address):
        """
        Assigns an address to this connection. This also implicitly sets
        the mode to manual (disables network autoconfiguration).
        """
        entry = self._get_first_address()
        entry[0] = dbus.UInt32(ip4addr_to_network_int(address))
        self._settings['ipv4']['method'] = 'manual'

    @property
    def netmask(self):
        """
        Returns the network mask of the connection in dotted quad
        notation, or None if the connection has no statically assigned
        address information.
        """
        if not self._has_address():
            return None

        entry = self._get_first_address()
        prefixlen = int(entry[1])
        return prefixlen_to_netmask(prefixlen)

    @netmask.setter
    def netmask(self, netmask):
        """
        Assigns the network mask for thisconnection. This also implicitly
        sets the mode to manual (disables network autoconfiguration).
        """
        entry = self._get_first_address()
        entry[1] = dbus.UInt32(netmask_to_prefixlen(netmask))
        self._settings['ipv4']['method'] = 'manual'

    @property
    def gateway(self):
        """
        Returns the IPv4 gateway assigned to this connection in
        dotted-quad notation, or None if the connection has no
        statically assigned address information.
        """
        if not self._has_address():
            return None

        entry = self._get_first_address()
        return network_int_to_ip4addr(entry[2])

    @gateway.setter
    def gateway(self, gateway):
        """
        Assigns a gateway to this connection. This also implicitly sets
        the mode to manual (disables network autoconfiguration).
        """
        entry =self._get_first_address()
        entry[2] = dbus.UInt32(ip4addr_to_network_int(gateway))
        self._settings['ipv4']['method'] = 'manual'

    @property
    def dns(self):
        """
        The assigned DNS server if the connection is manually configured
        or autoconfiguration should be forced to use a specific DNS server.

        Only accesses the first DNS address defined
        """
        try:
            value = self._settings['ipv4']['dns'][0]
            return network_int_to_ip4addr(value)
        except (IndexError, KeyError):
            return None

    @dns.setter
    def dns(self, address):
        if not 'ipv4' in self._settings:
            ipv4_settings = dbus.Dictionary({'ipv4': dbus.Dictionary({})})
            self._settings.update(ipv4_settings)
        self._settings['ipv4']['dns'] = dbus.Array([ip4addr_to_network_int(address)], signature='u')

    @property
    def dns_search(self):
        """
        The assigned DNS server if the connection is manually configured
        or autoconfiguration should be forced to use a specific DNS server.

        Only accesses the first DNS address defined
        """
        try:
            value = self._settings['ipv4']['dns-search'][0]
            return (value)
        except (IndexError, KeyError):
            return None

    @dns_search.setter
    def dns_search(self, name):
        if not 'ipv4' in self._settings:
            ipv4_settings = dbus.Dictionary({'ipv4': dbus.Dictionary({})})
            self._settings.update(ipv4_settings)
        self._settings['ipv4']['dns-search'] = dbus.Array([name], signature='s')
        try:
            xbmc.log(str(self._settings['ipv4']))
        except:
            syslog.syslog(str(self._settings['ipv4']))

    @property
    def dhcp_client_id(self):
        """
        The assigned DNS server if the connection is manually configured
        or autoconfiguration should be forced to use a specific DNS server.

        Only accesses the first DNS address defined
        """
        try:
            value = self._settings['ipv4']['dhcp-client-id'][0]
            return (value)
        except (IndexError, KeyError):
            return None

    @dhcp_client_id.setter
    def dhcp_client_id(self, name):
        if not 'ipv4' in self._settings:
            ipv4_settings = dbus.Dictionary({'ipv4': dbus.Dictionary({})})
            self._settings.update(ipv4_settings)
        self._settings['ipv4']['dhcp-client-id'] = dbus.String(name)

class WirelessSettings(BaseSettings):
    def __repr__(self):
        return "<WirelessSettings (%s)>" % ("DHCP" if self.auto else "Static")

    def __init__(self, properties=_default_settings_wireless):
        super(WirelessSettings, self).__init__(properties)


class WiredSettings(BaseSettings):
    def __repr__(self):
        return "<WiredSettings (%s)>" % ("DHCP" if self.auto else "Static")

    def __init__(self, properties=_default_settings_wired):
        super(WiredSettings, self).__init__(properties)

    @property
    def duplex(self):
        return self._settings['802-3-ethernet']['duplex']

    @duplex.setter
    def set_duplex(self, value):
        self._settings['802-3-ethernet']['duplex'] = value

class CdmaSettings(BaseSettings):
    def __repr__(self):
        return "<CdmaSettings (%s)>" % ("DHCP" if self.auto else "Static")

    def __init__(self, properties=_default_settings_cdma):
        super(CdmaSettings, self).__init__(properties)
