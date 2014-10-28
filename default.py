# declare file encoding
# -*- coding: utf-8 -*-

#  Copyright (C) 2012 S7MX1
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html

import sys
import os
import socket
import time
import pwd
import traceback
# addon constants
__author__ = "s7mx1"
__url__ = ""
__svn_url__ = ""
__credits__ = ""


reload(sys)
sys.setdefaultencoding('utf-8')

def log_exception(xbmc):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    xbmc.log(''.join('!! ' + line for line in lines),xbmc.LOGERROR)


if ( __name__ == "__main__" ):
        import xbmcaddon
        #import resources.lib.server as server
	__settings__ = xbmcaddon.Addon()
	__language__ = __settings__.getLocalizedString
	__version__    = __settings__.getAddonInfo('version')
	__cwd__        = __settings__.getAddonInfo('path')
        __firstrun__ = __settings__.getSetting("firstrun")
        NIGHTLY_URL="http://download.raspbmc.com/downloads/bin/xbmc/nightlies/"
        DISTRO = "Raspbmc"
        DISTRO_LINK = "www.raspbmc.com"
        USER=pwd.getpwuid(1000)[0]
        if USER == "pi":
            DISTRO = "Raspbmc"
            NIGHTLY_URL = "http://download.raspbmc.com/downloads/bin/xbmc/nightlies/"
            DISTRO_LINK = "www.raspbmc.com"
        if USER == "atv":
            DISTRO = "Crystalbuntu"
            NIGHTLY_URL = ""
            DISTRO_LINK = ""
        BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
        UPGRADE_PATH = os.path.join(os.getenv("HOME"),".upgrade")
        if os.path.isfile(UPGRADE_PATH):
            os.remove(UPGRADE_PATH)
        if not os.path.isdir(UPGRADE_PATH):
            os.makedirs(UPGRADE_PATH)
        sys.path.append (BASE_RESOURCE_PATH)
        if os.path.isdir("/scripts"):
            sys.path.append ("/scripts")
        socket.setdefaulttimeout(5)
        from upgrade import *
	from wifiscan import *
        from exception_handling import *
        if len(sys.argv) > 1:
            xbmc.log("script parameters: %s" % sys.argv)
            if sys.argv[1] == "upgrade":
                error= upgrade(NIGHTLY_URL,UPGRADE_PATH)
                if error != 0:
                    error_handling(error)
            if sys.argv[1] == "switch":
                try:
                    switch(UPGRADE_PATH)
                except:
                    onExceptionRaised()
            if sys.argv[1] == "delete":
                try:
                    delete(UPGRADE_PATH)
                except:
                    onExceptionRaised()
            if sys.argv[1] == "reset":
                if DISTRO == "Raspbmc":
                    RESET_IMAGE_URL="http://download.raspbmc.com/downloads/bin/ramdistribution/installer.img.gz"
                    RESET_IMAGE_FILE_PATH=os.path.join(os.getenv("HOME"),"installer.img.gz")
                try:
                    reset(RESET_IMAGE_URL,RESET_IMAGE_FILE_PATH)
                except:
                    onExceptionRaised()
	    if sys.argv[1] == "scannet":
               scannet()
            if sys.argv[1] == "password":
                error = set_password(__settings__)
                if error != 0:
                    error_handling(error)
            if sys.argv[1] == "Quit":
                xbmc.executebuiltin(sys.argv[1])
                #from power import *
                #lirc_workaround(sys.argv[1])
            if sys.argv[1] == "Powerdown":
                xbmc.executebuiltin(sys.argv[1])
                #from power import *
                #lirc_workaround(sys.argv[1])
            if sys.argv[1] == "Reboot":
                xbmc.executebuiltin(sys.argv[1])
                #from power import *
                #lirc_workaround(sys.argv[1])




        if len(sys.argv) == 1:
            xbmc.executebuiltin('XBMC.Notification('+'"'+DISTRO+' Settings Addon by S7mx1", "Visit '+DISTRO_LINK+' for more info",5000,"'+'")')
            try:
                last_run = int(__settings__.getSetting("lastrun"))
            except:
                last_run = 0

            from sys_config import *
            from switches import *
            current_time = int(round(time.time()))
            # only reload network settings if last run is more than 1 hour ago
            if current_time - last_run >= 3600:
                if DISTRO == "Raspbmc":
                    sys_config={}
                    try:
                        sys_config = load_sysconfig()
                    except:
                        onExceptionRaised()

                    for key in  ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.isp","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt","sys.config.decode.mpg2","sys.config.decode.wvc1","sys.config.decode.dts","sys.config.decode.ac3"):
                         exec "try: __settings__.setSetting(\"%s\",str(sys_config[\"%s\"]))\nexcept: log_exception(xbmc)" % (key,key)
                    try:
                        if sys_config["sys.config.disable.overscan"] == "1":
                            __settings__.setSetting("sys.config.disable.overscan","true")
                        else:
                            __settings__.setSetting("sys.config.disable.overscan","false")
                    except:
                       log_exception(xbmc)
                    freq_from_file={}
                    try:
                        for key in  ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.isp","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt"):
                            freq_from_file[key]=sys_config[key]
                    except:
                        log_exception(xbmc)
                from nm_util import *
                nm = NetworkManager()
                for conn in nm.connections:
                     xbmc.log("conn: "+str(conn))
                     xbmc.log("conn.settings: "+str(conn.settings))
                     xbmc.log("conn.settings.type: "+str(conn.settings.type))
                nic_list=[]
                try:
                    nic_list  = display_connection(nm)
                except:
                    onExceptionRaised()

                if len(nic_list) > 0:
                    nic_to_configure=nic_list[0]
                    for nic in nic_list:
                        if nic.get('type') == '802-3-ethernet':
                            try:
                                __settings__.setSetting("nm.dhcp",nic['dhcp'])
                            except:
                                log_exception(xbmc)
                            try:
                                __settings__.setSetting("nm.mac",nic['mac'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.address",nic['address'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.netmask",nic['netmask'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.gateway",nic['gateway'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.dns",nic['dns'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.id",nic['id'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.uuid",nic['uuid'])
                            except:
                                pass
                            try:
                                __settings__.setSetting("nm.search",nic['search'])
                            except:
                                pass
                else:
                    xbmc.executebuiltin('XBMC.Notification("'+"NO Active Network Devices found"+'",You may not be able to change network settings,3500,"'+'")')
            old_network_settings, old_system_settings, old_service_settings, old_switch_settings =load_settings(__settings__,DISTRO)
            
            #if "search" in old_network_settings:
            #    try:
            #        __settings__.setSetting("nm.search",nic_list[0]['search'])
            #    except:
            #        log_exception(xbmc)
            __settings__.setSetting("nm.force_update","false")
            try:
                __settings__.openSettings()
            except KeyboardInterrupt,SystemExit:
                sys.exit(0)
            new_network_settings, new_system_settings, new_service_settings, new_switch_settings =load_settings(__settings__,DISTRO)
            if old_network_settings != new_network_settings or new_network_settings["nm.force_update"] == "true":
                __settings__.setSetting("nm.force_update","false")
                xbmc.executebuiltin('XBMC.Notification("'+"Network Configuration Updated"+'",Reconfiguring Network,3500,"'+'")')
                if "nm" not in vars():
                    from nm_util import *
                    nm = NetworkManager()                
                #nm.reload
                try:
                    re_code=modify_connection(new_network_settings,nm)
                    if re_code == -11:
                        import syslog
                        syslog.syslog("network settings from"+DISTRO+ "addon: "+str(new_network_settings))
                        conn_state = None
                        for conn in nm.connections:
                            for interface in nm.devices:
                                if str(conn.settings.mac_address) == str(interface.hwaddress):
                                    conn_state=int(interface.proxy.Get(NM_DEVICE, "State"))
                                    syslog.syslog("[%s] device state: %s" % (str(conn),str(conn_state)))
                                    if conn_state == 100:
                                        syslog.syslog("[%s] device address: %s" % (str(conn),str(interface.ip4config.addresses[0][0])))
                                        syslog.syslog("[%s] device netmask: %s" % (str(conn),str(interface.ip4config.addresses[0][1])))
                                        syslog.syslog("[%s] device gateway: %s" % (str(conn),str(interface.ip4config.addresses[0][2])))
                                        syslog.syslog("[%s] device dns: %s" % (str(conn),str(interface.ip4config.name_servers[0])))
                                    break
                            for key in ("auto","address","conn_type","dhcp_client_id","dns","dns_search","duplex","gateway","id","mac_address","netmask","type","uuid"):
                                if hasattr(conn.settings,key):
                                    exec "var_string=conn.settings.%s" % key
                                    syslog.syslog("[%s] connection property %s: %s" %(str(conn),key,str(var_string)))
                        onNoNetworkInterfaceFoundRaised()
                    elif re_code == 10:
                        xbmc.executebuiltin('XBMC.Notification("'+"Network Configuration Applied"+'",,1500,"'+'")')
                        nm.proxy.Enable(dbus.Boolean(0))
                        nm.proxy.Enable(dbus.Boolean(1))
                except:
                    onExceptionRaised()

            RESTART_ACTION,RESTART_MESSAGE,REBOOT_ACTION,REBOOT_MESSAGE = set_switch(new_switch_settings,DISTRO)

            if old_service_settings != new_service_settings:
                services={}
                for item in old_service_settings.items():
                    if item[1] != new_service_settings[item[0]]:
                        services[item[0]]=new_service_settings[item[0]]
                try:
                    set_services(services)
                except:
                    onExceptionRaised()
                xbmc.executebuiltin('XBMC.Notification("'+"Service Configuration Updated"+'",Reconfiguring Service,3500,"'+'")')

            if DISTRO == "Raspbmc":
                if __settings__.getSetting("sys.config.freq.manual") == "false":
                    if "freq_from_file" in vars():
                        for key in  ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.isp","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt"):
                            old_system_settings[key] = freq_from_file[key]

                if old_system_settings != new_system_settings:
                    time_stamp=str(int(round(time.time())))
                    try:
                        set_sysconfig(new_system_settings,time_stamp)
                    except:
                        onExceptionRaised()
                    if __settings__.getSetting("sys.config.freq.manual") == "false":
                        for key in  ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.isp","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt"):
                            __settings__.setSetting(key,str(new_system_settings[key]))
                    
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("Configuration updated")

            __settings__.setSetting("lastrun",str(int(round(time.time()))))

            if __firstrun__ == "true":
                __settings__.setSetting("firstrun","false")
            
            if REBOOT_ACTION:
                dialog = xbmcgui.Dialog()
                dialog_message = []
                index=0
                for line in REBOOT_MESSAGE:
                    dialog_message.append(line)
                    if index == 2:
                        break
                    index += 1
                if index <= 2:
                    for line in RESTART_MESSAGE:
                        dialog_message.append(line)
                        if index == 2:
                            break
                        index += 1
                while index <= 2:
                    dialog_message.append("")
                    index += 1

                ret = dialog.yesno(DISTRO+'     Do you want to restart XBMC now?', dialog_message[0] ,dialog_message[1], dialog_message[2])
                if ret:
                    xbmc.executebuiltin('Reboot')

            if RESTART_ACTION:
                dialog = xbmcgui.Dialog()
                dialog_message = []
                index=0
                for line in RESTART_MESSAGE:
                    dialog_message.append(line)
                    if index == 2:
                        break
                    index += 1
                while index <= 2:
                    dialog_message.append("")
                    index += 1
                
                ret = dialog.yesno(DISTRO+'     Do you want to restart XBMC now?', dialog_message[0] ,dialog_message[1], dialog_message[2])
                if ret:
                    xbmc.executebuiltin('Quit')
