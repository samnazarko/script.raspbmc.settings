#!/usr/bin/env python2

# Copyright 2010 Aerva, Inc
# Copyright 2010 Gavin Bisesi
# Copyright 2010 Mark Renouf
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

import sys
import dbus
from networkmanager import *
from ipaddr import *
import uuid
try:
    import xbmc
except:
    import syslog


nm = None

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def device_for_hwaddr(hwaddr, nm=NetworkManager()):
    for device in nm.devices:
        if device.hwaddress == hwaddr:
            return device

def device_by_name(name, nm=NetworkManager()):
    """Return the Device object for a given device name (eg. 'eth0' 'wlan0' 'ttyUSB1')"""
    try:
        return [dev for dev in nm.devices if str(dev.interface) == name][0]
    except IndexError:
        return None

def connections_for_device(device, nm=NetworkManager()):
    hwaddr = None
    for device in nm.devices:
        if device.interface == device:
            hwaddr = device.hwaddr
            break
    if hwaddr is None:
        return None

    conns = []
    for conn in nm.connections:
        if conn.settings.mac_address == hwaddr:
            conns.append(conn)
    return conns

def parse_connection_settings(args):
    """Parses position arguments for connection settings

    Format is in the form of [[token] <value>, ...] where the value
    may be optional for some boolean options. Any problems are raised
    as a ValueError with a user-friendly message.
    """
    options = {"auto": True}
    pos = 0
    # ip-based options (for static config, mostly)
    ipv4_opts = ('ip','mask','gw','dns',)
    # Options passed with direct values.
    #   Currently used with CDMA
    string_opts = ('num','user','pass',)
    # Auto is the 'default' option
    allowed_opts = ['auto',]
    allowed_opts.extend(ipv4_opts)
    allowed_opts.extend(string_opts)

    while pos < len(args):
        opt = args[pos]
        if not opt in allowed_opts:
            raise ValueError("Invalid option '%s'" % (opt))

        if opt != "auto":
            pos += 1
            # The rest of these require a value in the next position
            if pos == len(args):
                raise ValueError("Missing value for option '%s'" % (opt))

            value = args[pos]
            try:
                if opt in ipv4_opts:
                    options[opt] = IPAddress(value,version=4)

            except IPv4IpValidationError, e:
                raise ValueError("Invalid value for '%s': %s" % (opt, e))

        if opt in string_opts:
            options[opt] = dbus.String(value)

        if 'ip' in options:
            options['auto'] = False

        pos += 1

    # TODO: Update for CDMA
    settings_usage = "settings: \"[auto | ip <address> mask <address> gw <address> dns <dns>]"

    if not options['auto']:
        required_opts = ('ip', 'mask', 'gw', 'dns')
        for opt in required_opts:
            if not opt in options:
                raise ValueError("Settings: Missing value for '%s'\n" % opt + settings_usage)

    return options

def display_connection(nm):
    types = {'802-3-ethernet':'Wired (Ethernet)',
             '802-11-wireless':'Wireless (Wifi)',
             'cdma':'CDMA (Mobile Broadband)',}

    #print "UUID:     %s" % conn.settings.uuid
    #print "Id:       %s" % conn.settings.id
    #print "Type:     %s" % (types[conn.settings.type])
    nic_list=[]
    type2desc = {1:'802-3-ethernet', 2:'802-11-wireless'}
    for conn in nm.connections:
        nic={}
        if conn.settings.mac_address is not None:
            device = device_for_hwaddr(conn.settings.mac_address)
            #print device
            #print "Device:   %s" % ("Unknown" if device is None else device.interface)
        if conn.settings.auto:
            nic['dhcp']="true"
        else:
            nic['dhcp']="false"
        for interface in nm.devices:
            if str(conn.settings.mac_address) == str(interface.hwaddress):
                dev_type_int = interface.proxy.Get(NM_DEVICE, "DeviceType")
                dev_type = type2desc.get(dev_type_int, None)
#            if conn.settings.type == dev_type:
                dev_state = interface.proxy.Get(NM_DEVICE, "State")
                if dev_state == 100: # NM_DEVICE_STATE_ACTIVATED
                     nic['address'] =interface.ip4config.addresses[0][0]
                     nic['netmask'] = interface.ip4config.addresses[0][1]
                     nic['gateway']=interface.ip4config.addresses[0][2]
                     nic['dns'] = interface.ip4config.name_servers[0]
                     nic['mac'] = interface.hwaddress
                     nic['id'] = conn.settings.id
                     nic['uuid'] = conn.settings.uuid
                     nic['type'] = dev_type
                     try:
                         nic['search'] = conn.settings.dns_search
                     except:
                         pass
        #if nic != {}:
        #if nic.get('type') == '802-3-ethernet':
        nic_list.append(nic)
    return nic_list




def list_connections(options, nm=NetworkManager()):
    filt = make_connection_filter(options)
    for conn in filter(filt, nm.connections):
        display_connection(conn,nm)

def list_active_connections(options, nm=NetworkManager()):
    types = {'802-3-ethernet':'Wired (Ethernet)',
             '802-11-wireless':'Wireless (Wifi)',
             'cdma':'CDMA (Mobile Broadband)',}
    for active in nm.active_connections:
        print "UUID:     %s" % active.connection.settings.uuid
        print "Id:       %s" % active.connection.settings.id
        print "State:    %s" % active.state
        #print "Default:  %s" % active.default
        print "Type:     %s" % (types[active.connection.settings.type])
        print "Device:   %s" % (",".join([device.interface for device in active.devices]))
        #print "Settings from %s:" % active.service_name

        if active.connection.settings.auto:
            print "Address:  auto (DHCP)"
        else:
            print "Address:  %s" % active.connection.settings.address
            print "Netmask:  %s" % active.connection.settings.netmask
            print "Gateway:  %s" % active.connection.settings.gateway

        if active.connection.settings.dns is not None:
            print "DNS:      %s"  % active.connection.settings.dns

def create_connection(parser, options, args, nm=NetworkManager()):
    types = {
        'wired': DeviceType.ETHERNET,
        'wireless': DeviceType.WIFI,
        'cdma': DeviceType.CDMA,
    }

    if not options.id:
        parser.error("Create: you must supply a connection id (--id=\"MyConnection\").")

    if not options.device and not options.type:
        parser.error("Create: you must specify a device name or connection type.")

    device = None
    # find the device with the specified interface name ('eth0', etc)
    # TODO: use dict lookup table
    if options.device:
        for d in nm.devices:
            if d.interface == options.device:
                device = d

    # if a device was specified, create a connection of the same type
    # otherwise use the type that was supplied through the 'type' option
    type = device.type if device else types[options.type]

    # Create a settings object of the appropriate type
    settings = None

    # FIXME: Smelly (Factory pattern to fix?)
    if type == DeviceType.ETHERNET:
        settings = WiredSettings()
    elif type == DeviceType.WIFI:
        settings = WirelessSettings()
    elif type == DeviceType.CDMA:
        settings = CdmaSettings()

    settings.uuid = str(uuid.uuid4())

    # apply the settings
    settings.id = options.id
    if device is not None:
        settings.device = device
        # TODO: Add Device::get_hwaddress()
        if type == DeviceType.ETHERNET:
            settings.mac_address = device.hwaddress

    # FIXME: Code duplication vs modify_connection()
    try:
        params = parse_connection_settings(args)
    except ValueError, e:
        parser.error(e)

    if params['nm.auto']:
        settings.set_auto()
    else:
        settings.address = params['nm.ip']
        settings.netmask = params['nm.mask']
        settings.gateway = params['nm.gw']

    possible_settings = ('dns','num','user','pass')
    for s in possible_settings:
        if s in params:
            setattr(settings, s, params["nm."+s])

    nm.add_connection(settings)

def modify_connection(params, nm=NetworkManager()):
    types = {'wired': '802-3-ethernet',
             'wireless': '802-11-wireless',
             'cdma':'cdma',}
    type2desc = {1:'802-3-ethernet', 2:'802-11-wireless'}
    #uuid = params['nm.uuid']
    #conn = None
    #if uuid != "":
    #    conn = nm.get_connection(uuid)
    #if conn == None:
    conn_list=[]
    for conn in nm.connections:
        for interface in nm.devices:
            if str(conn.settings.mac_address) == str(interface.hwaddress):
                dev_state = interface.proxy.Get(NM_DEVICE, "State")
                dev_type_int = interface.proxy.Get(NM_DEVICE, "DeviceType")
                dev_type = type2desc.get(dev_type_int, None)
                conn_list.append((conn,dev_type,int(dev_state)))
                break
    try:
        xbmc.log("conn_list: "+str(conn_list))
    except:
        syslog.syslog("conn_list: "+str(conn_list))
    active_conn_list=[]
    for a in conn_list:
        if a[2] >=20 : # http://projects.gnome.org/NetworkManager/developers/api/09/spec.html#type-NM_DEVICE_STATE
                              # any states other than NM_DEVICE_STATE_UNKNOWN
                              # NM_DEVICE_STATE_UNMANAGED
            active_conn_list.append(a)
    #for b in active_conn_list:
    #    conn = b[0]
    #    if b[1] == type2desc[1]: # Wired Network
    #        break
    #if conn == None:
    #    for c in conn_list:
    #        conn = c[0]
    #        if c[1] == type2desc[1]: # Wired Networ          
    #            break
    RETURN_CODE = -11
    if len(active_conn_list) > 0:
        for a in active_conn_list:
            conn = a[0]
            settings = conn.settings
            old_settings = str(settings._settings)
            if a[1] == type2desc[1]: # Wired Network
                if params['nm.dhcp'] == "false":
                    address = params['nm.address']
                    netmask = params['nm.netmask']
                    gateway = params['nm.gateway']
                    dns = params['nm.dns']
                    dns_search = params['nm.search']
            if a[1] == type2desc[2]: # Wireless Network
                if params['nm.wifi.dhcp'] == "false":
                    address = params['nm.wifi.address']
                    netmask = params['nm.wifi.netmask']
                    gateway = params['nm.wifi.gateway']
                    dns = params['nm.wifi.dns']
                    dns_search = params['nm.wifi.search']
                # 802-11-wireless
                if params["nm.wifi.5GOnly"] == "true":
                    # 5GHz 802.11a
                    band = "a"
                else:
                    # 2.4GHz 802.11
                    band = "bg"
                ## WiFi network mode
                if params["nm.wifi.adhoc"] == "true":
                    mode = "adhoc"
                else:
                    mode = "infrastructure"
                security = "802-11-wireless-security"
                key_mgmt = "none"
                # None
                if params["nm.wifi.security"] == "0":
                    security = ""
                    key_mgmt = ""
                # WEP (Open Key)
                if params["nm.wifi.security"] == "1":
                    key_mgmt = "none"
                    auth_alg = "open"
                # WEP (Shared Key)
                if params["nm.wifi.security"] == "2":
                    key_mgmt = "none"
                    auth_alg = "shared"
                # Dynamic WEP
                if params["nm.wifi.security"] == "3":
                    key_mgmt = "ieee8021x"
                # WPA/WPA2
                if params["nm.wifi.security"] == "4":
                    if mode == "adhoc":
                        key_mgmt = "wpa-none"
                    else:
                        key_mgmt = "wpa-psk"

                if "802-11-wireless" in settings._settings:
                    try:
                        xbmc.log(a[1]+" 802-11-wireless old: "+str(settings._settings['802-11-wireless']))
                    except:
                        syslog.syslog(a[1]+" 802-11-wireless old: "+str(settings._settings['802-11-wireless']))
                else:
                    settings._settings['802-11-wireless'] = dbus.Dictionary(signature='sv')

                # clear 802-11-wireless settings
                # settings._settings['802-11-wireless'] = dbus.Dictionary(signature='sv')
                    
                settings._settings['802-11-wireless']['security']=dbus.String(security)
                if security == "":
                    del(settings._settings['802-11-wireless']['security'])
                settings._settings['802-11-wireless']['mode']=dbus.String(mode)
                settings._settings['802-11-wireless']['band']=dbus.String(band)
                SSID=[]
                for c in params["nm.wifi.ssid"]:
                    SSID.append(dbus.Byte(int(ord(c))))
                settings._settings['802-11-wireless']['ssid']=dbus.Array(SSID,signature='y')

                if "802-11-wireless-security" in settings._settings:
                    try:
                        xbmc.log(a[1]+" 802-11-wireless-security old: "+str(settings._settings['802-11-wireless-security']))
                    except:
                        syslog.syslog(a[1]+" 802-11-wireless-security old: "+str(settings._settings['802-11-wireless-security']))
                else:
                    if key_mgmt != "":
                        settings._settings['802-11-wireless-security'] = dbus.Dictionary(signature='sv')

                # clear 802-11-wireless-security settings
                # settings._settings['802-11-wireless-security'] = dbus.Dictionary(signature='sv')
                if key_mgmt == "" and "802-11-wireless-security" in settings._settings:
                    del(settings._settings['802-11-wireless-security'])
                    CONFIG_DIFFERENCE = True


                if key_mgmt != "":
                    settings._settings['802-11-wireless-security']['key-mgmt']=dbus.String(key_mgmt)
                if key_mgmt == "none":
                    settings._settings['802-11-wireless-security']['auth-alg']=dbus.String(auth_alg)
                    if len(params["nm.wifi.key"]) > 0:
                        settings._settings['802-11-wireless-security']['wep-key0']=dbus.String(params["nm.wifi.key"])
                        settings._settings['802-11-wireless-security']['wep-key1']=dbus.String(params["nm.wifi.key"])
                elif key_mgmt != "":
                    if len(params["nm.wifi.key"]) > 0:
                        settings._settings['802-11-wireless-security']['psk']=dbus.String(params["nm.wifi.key"])

            if not "ipv6" in settings._settings:
                settings._settings['ipv6'] = dbus.Dictionary(signature='sv')
            settings._settings['ipv6']['method'] = dbus.String("ignore")

            if "ipv4" in settings._settings:
                try:
                    xbmc.log(a[1]+" ipv4 old: "+str(settings._settings['ipv4']))
                except:
                    syslog.syslog(a[1]+" ipv4 old: "+str(settings._settings['ipv4']))
            else:
                settings._settings['ipv4'] = dbus.Dictionary(signature='sv')

            DHCP = False
            if a[1] == type2desc[1] and params['nm.dhcp'] == "true":
                DHCP = True
            if a[1] == type2desc[2] and params['nm.wifi.dhcp'] == "true":
                DHCP = True
            if DHCP:
                settings.set_auto()
                if  params['nm.uid.enable'] == "true":
                    mac_list = settings.mac_address.split(":")
                    uid = "xbmc-"+mac_list[4].lower()+mac_list[5].lower()
                else:
                    uid = "xbmc"
                settings._settings['ipv4']['dhcp-client-id']=dbus.String(uid)
                settings._settings['ipv4']['dhcp-hostname']=dbus.String(uid)
                settings._settings['ipv4']['dhcp-send-hostname']=dbus.Boolean(1)
            else:
                if not 'addresses' in settings._settings['ipv4']:
                    settings._settings['ipv4']['addresses'] = dbus.Array([], signature='au')
                settings.address = address
                settings.netmask = netmask
                settings.gateway = gateway
                settings.dns = dns
                settings._settings['ipv4']['dns-search']=dbus.Array([dns_search],signature='s')

            #conn.proxy.Update(settings._settings, dbus_interface=NM_SETTINGS_CONNECTION)
            if old_settings != str(settings._settings):
                try:
                    xbmc.log(str(settings.type))
                    if "ipv4" in settings._settings:
                        xbmc.log(a[1]+"ipv4 new: "+str(settings._settings['ipv4']))
                    if "802-11-wireless" in settings._settings:
                        xbmc.log(a[1]+"802-11-wireless: "+str(settings._settings['802-11-wireless']))
                    if "802-11-wireless-security" in settings._settings:
                        xbmc.log(a[1]+"802-11-wireless-security: "+str(settings._settings['802-11-wireless-security']))
                except:
                    syslog.syslog(str(settings.type))
                    if "ipv4" in settings._settings:
                        syslog.syslog(a[1]+"ipv4 new: "+str(settings._settings['ipv4']))
                    if "802-11-wireless" in settings._settings:
                        syslog.syslog(a[1]+"802-11-wireless new: "+str(settings._settings['802-11-wireless']))
                    if "802-11-wireless-security" in settings._settings:
                                            syslog.syslog(a[1]+"802-11-wireless-security new: "+str(settings._settings['802-11-wireless-security']))
                conn.update(settings)
                # return 10 if settings need to update
                RETURN_CODE = 10
            else:
                # return 0 if settings do not need to update
                RETURN_CODE = 0

    return RETURN_CODE

def delete_connection(parser, options, nm=NetworkManager()):
    uuid = options.ensure_value('uuid', None)

    if uuid is None:
        parser.error("Delete: you must supply a connection uuid.")

    conn = nm.get_connection(uuid)
    if conn is None:
        parser.error("Delete: the uuid does not match an existing connection")

    conn.delete()

def activate_connection(params, nm=NetworkManager()):
    uuid = params['nm.uuid']

    conn = nm.get_connection(uuid)
    device = None

    #print "Devices: %s" % nm.devices
    types = {
        DeviceType.ETHERNET: '802-3-ethernet',
        DeviceType.WIFI: '802-11-wireless',
        DeviceType.CDMA: 'cdma',
    }

    for d in nm.devices:
        try:
            if types[d.type] == conn.settings.type:
                device = d
                break
        except KeyError:
            raise UnsupportedConnectionType("Activate: connection type '%s' is not supported" % d.type)

    if device is None:
        parser.error("Activate: there are no network devices "
                     "available for this type of connection")

    try:
        nm.activate_connection(conn, device)
    except dbus.exceptions.DBusException, e:
        if str(e).startswith('org.freedesktop.NetworkManager.UnmanagedDevice'):
            parser.error("Activate: device (%s) not currently managed" % device.interface)
        else:
            raise

def deactivate_connection(params, nm=NetworkManager()):
    uuid = params['nm.uuid']

    for active in nm.active_connections:
        if active.connection.settings.uuid == uuid:
            nm.deactivate_connection(active.proxy)
            return

