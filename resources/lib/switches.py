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

import os
try:
    import xbmc
except:
    import syslog

def clear_resolution_settings(XML):
    import xml.etree.ElementTree as ET
    if os.path.isfile(XML):
        tree = ET.parse(XML)
        root = tree.getroot()
        for child in root:
            if child.tag == "resolutions":
                root.remove(child)
        tree.write(XML)


def set_switch(sys_dict,DISTRO):
    AUTO_UPGRADE_FILE= os.path.join(os.getenv("HOME"), ".noupgrades")
    UPGRADE_PATH = os.path.join(os.getenv("HOME"),".upgrade")
    GUI_SETTINGS = os.path.join(os.getenv("HOME"),".xbmc","userdata","guisettings.xml")
    XBMC_NOLIMIT_FILE = os.path.join(os.getenv("HOME"),".nolimit")
    XBMC_AUDIOENGINE_FILE = os.path.join(os.getenv("HOME"),".audioengine")
    XBMC_SOUNDCARD_FILE = os.path.join(os.getenv("HOME"), ".omxalsa")
    XBMC_NOSHUTWARN_FILE = os.path.join(os.getenv("HOME"), ".nowarning")
    XBMC_KHEAD_FILE = os.path.join(os.getenv("HOME"), ".kernelheaders")
    XBMC_OCV_FILE = os.path.join(os.getenv("HOME"), ".opencv")
    XBMC_TON_FILE = os.path.join(os.getenv("HOME"), ".tonido")
    REMOTE_REPEAT_FILTER_FILE = os.path.join(os.getenv("HOME"),".no-repeat-filter")
    REMOTE_FOLDER = "/etc/lirc"
    REBOOT_ACTION = False
    REBOOT_MESSAGE = []
    RESTART_ACTION = False
    RESTART_MESSAGE = []
    if "sys.upgrade" in sys_dict:
        if sys_dict["sys.upgrade"] == "true":
            if os.path.isfile(AUTO_UPGRADE_FILE):
                os.remove(AUTO_UPGRADE_FILE)
                try:
                    xbmc.executebuiltin('XBMC.Notification("'+DISTRO+" updates are enabled"+'",,2000,"'+'")')
                except:
                    syslog.syslog(DISTRO+" updates are enabled")

        else:
            if not os.path.isfile(AUTO_UPGRADE_FILE):
                f=open(AUTO_UPGRADE_FILE,'w')
                f.close()
                try:
                    xbmc.executebuiltin('XBMC.Notification("'+DISTRO+" updates are disabled"+'",,2000,"'+'")')
                except:
                    syslog.syslog(DISTRO+" updates are disabled")

    if "remote.filter" in sys_dict:
        if sys_dict["remote.filter"]== "false":
            if not os.path.isfile(REMOTE_REPEAT_FILTER_FILE):
                f=open(REMOTE_REPEAT_FILTER_FILE,'w')
                f.close()
                REBOOT_ACTION = True
                REBOOT_MESSAGE.append("IR Remote repeat filter is disabled")
        else:
            if os.path.isfile(REMOTE_REPEAT_FILTER_FILE):
                os.remove(REMOTE_REPEAT_FILTER_FILE)
                REBOOT_ACTION = True
                REBOOT_MESSAGE.append("IR Remote repeat filter is restored")

    if DISTRO == "Raspbmc":
        if "sys.xbmc.res" in sys_dict:
            if sys_dict["sys.xbmc.res"] == "true":
                if not os.path.isfile(XBMC_NOLIMIT_FILE):
                    f=open(XBMC_NOLIMIT_FILE,'w')
                    f.close()
                    try:
                        clear_resolution_settings(GUI_SETTINGS)
                    except:
                        pass
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("XBMC Resolution limit is removed")
                    #xbmc.executebuiltin('XBMC.Notification('+'"XBMC Resolution limit is removed","Please restart xbmc for it to take effect",2000,"'+'")')
            else:
                if os.path.isfile(XBMC_NOLIMIT_FILE):
                    os.remove(XBMC_NOLIMIT_FILE)
                    clear_resolution_settings(GUI_SETTINGS)
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("XBMC Resolution limit is restored")
                    #xbmc.executebuiltin('XBMC.Notification('+'"XBMC Resolution limit is restored","Please restart xbmc for it to take effect",2000,"'+'")')

        if "sys.xbmc.ae" in sys_dict:
            if sys_dict["sys.xbmc.ae"] == "true":
                if not os.path.isfile(XBMC_AUDIOENGINE_FILE):
                    f=open(XBMC_AUDIOENGINE_FILE,'w')
                    f.close()
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("Audio Engine is enabled")
            else:
                if os.path.isfile(XBMC_AUDIOENGINE_FILE):
                    os.remove(XBMC_AUDIOENGINE_FILE)
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("Audio Engine is disabled")

	    if "sys.xbmc.sc" in sys_dict:
	        if sys_dict["sys.xbmc.sc"] == "true":
                    if not os.path.isfile(XBMC_SOUNDCARD_FILE):
                        f=open(XBMC_SOUNDCARD_FILE,'w')
                        f.close()
                        RESTART_ACTION = True
                        RESTART_MESSAGE.append("ALSA support is enabled")
            else:
	         if os.path.isfile(XBMC_SOUNDCARD_FILE):
		         os.remove(XBMC_SOUNDCARD_FILE)
		         RESTART_ACTION = True
		         RESTART_MESSAGE.append("ALSA support is disabled")

        if "sys.xbmc.shut" in sys_dict:
            if sys_dict["sys.xbmc.shut"] == "true":
                if not os.path.isfile(XBMC_NOSHUTWARN_FILE):
                    f=open(XBMC_NOSHUTWARN_FILE,'w')
                    f.close()
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("Shutdown warnings are disabled")
            else:
                if os.path.isfile(XBMC_NOSHUTWARN_FILE):
                    os.remove(XBMC_NOSHUTWARN_FILE)
                    RESTART_ACTION = True
                    RESTART_MESSAGE.append("Shutdown warnings are enabled")
                    
        if "sys.xbmc.headers" in sys_dict:
            if sys_dict["sys.xbmc.headers"] == "true":
                if not os.path.isfile(XBMC_KHEAD_FILE):
                    f=open(XBMC_KHEAD_FILE,'w')
                    f.close()
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("Kernel headers are available")
            else:
                if os.path.isfile(XBMC_KHEAD_FILE):
                    os.remove(XBMC_KHEAD_FILE)
                    RESTART_ACTION = False          
                    
        if "sys.xbmc.tonido" in sys_dict:
            if sys_dict["sys.xbmc.tonido"] == "true":
                if not os.path.isfile(XBMC_TON_FILE):
                    f=open(XBMC_KTON_FILE,'w')
                    f.close()
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("Tonido is ready to install")
            else:
                if os.path.isfile(XBMC_TON_FILE):
                    os.remove(XBMC_TON_FILE)
                    RESTART_ACTION = False                                  
                    

        if "remote.filter" in sys_dict:
            if sys_dict["remote.filter"]== "false":
                if not os.path.isfile(REMOTE_REPEAT_FILTER_FILE):
                    f=open(REMOTE_REPEAT_FILTER_FILE,'w')
                    f.close()
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("IR Remote repeat filter is disabled")
            else:
                if os.path.isfile(REMOTE_REPEAT_FILTER_FILE):
                    os.remove(REMOTE_REPEAT_FILTER_FILE)
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("IR Remote repeat filter is restored")

        if "remote.gpio.enable" in sys_dict and "remote.gpio.profile" in sys_dict:
            if sys_dict["remote.gpio.enable"] == "true" and os.path.isfile("/usr/bin/sudo"):
                REMOTE_INDEX=int(sys_dict["remote.gpio.profile"])
                REMOTE_LIST={0:"custom-lircd.conf", 1:"xbox-lircd.conf", 2:"rc6-mce-lircd.conf",
                             3:"atilibusb-lircd.conf", 4:"apple-silver-A1294-lircd.conf",
                             5:"ttusbir-lircd.conf", 6:"philips-srm-7500-lircd.conf",
                             7:"samsung-lircd.conf", 8:"kls-1.6-lircd.conf", 9:"hauppage45-pvr350-lircd.conf"}
                if os.path.isfile(os.path.join(REMOTE_FOLDER,REMOTE_LIST[0])):
                    if not os.path.islink(os.path.join(REMOTE_FOLDER,REMOTE_LIST[0])):
                        os.system("sudo rm "+os.path.join(REMOTE_FOLDER,REMOTE_LIST[0]))
                if not os.path.isfile(os.path.join(REMOTE_FOLDER,REMOTE_LIST[0])):
                    os.system("sudo ln -s /home/pi/lircd.conf "+os.path.join(REMOTE_FOLDER,REMOTE_LIST[0]))
                #    if os.path.isfile(os.path.join(REMOTE_FOLDER,"lircd.conf")):
                #        if not os.path.islink(os.path.join(REMOTE_FOLDER,"lircd.conf")):
                #            os.system("sudo cp -a "+os.path.join(REMOTE_FOLDER,"lircd.conf")+" "+os.path.join(REMOTE_FOLDER,REMOTE_LIST[0]))
                #    if not os.path.isfile(os.path.join(REMOTE_FOLDER,REMOTE_LIST[0])):
                #        os.system("sudo touch "+os.path.join(REMOTE_FOLDER,REMOTE_LIST[0]))
                if os.path.isfile(os.path.join(REMOTE_FOLDER,"lircd.conf")):
                    if os.path.islink(os.path.join(REMOTE_FOLDER,"lircd.conf")):
                        if os.path.realpath(os.path.join(REMOTE_FOLDER,"lircd.conf")) != os.path.join(REMOTE_FOLDER,REMOTE_LIST[REMOTE_INDEX]):
                            os.system("sudo rm "+os.path.join(REMOTE_FOLDER,"lircd.conf"))
                    else:
                        os.system("sudo rm "+os.path.join(REMOTE_FOLDER,"lircd.conf"))

                if not os.path.isfile(os.path.join(REMOTE_FOLDER,"lircd.conf")):
                    os.system("sudo ln -s "+os.path.join(REMOTE_FOLDER,REMOTE_LIST[REMOTE_INDEX])+" "+os.path.join(REMOTE_FOLDER,"lircd.conf"))
                    REBOOT_ACTION = True
                    REBOOT_MESSAGE.append("GPIO IR Remote configuration file updated")

    return     RESTART_ACTION,RESTART_MESSAGE,REBOOT_ACTION,REBOOT_MESSAGE
