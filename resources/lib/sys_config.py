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

import StringIO
import ConfigParser

def float2int(value):
    return int(round(float(value)))

def load_settings(__settings__,DISTRO):
        dict_nm={}
        dict_sys={}
        dict_service={}
        dict_switches={}
        for key in ("nm.dhcp","nm.mac","nm.address","nm.netmask","nm.gateway","nm.dns","nm.id","nm.uuid","nm.force_update","nm.search","nm.uid.enable"):
            exec "dict_nm[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
        for key in ("nm.wifi.5GOnly","nm.wifi.address","nm.wifi.adhoc","nm.wifi.dhcp","nm.wifi.dns","nm.wifi.gateway","nm.wifi.key","nm.wifi.netmask","nm.wifi.search","nm.wifi.security","nm.wifi.ssid"):
            exec "dict_nm[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
        for key in ("sys.service.ftp","sys.service.ssh","sys.service.samba","sys.service.remote","sys.service.cron","sys.service.tvh", "sys.service.boblight", "sys.service.surveil", "sys.service.vnc", "sys.service.sab", "sys.service.del"):
            exec "dict_service[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
        for key in ("sys.upgrade","remote.filter"):
            exec "dict_switches[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
        if DISTRO == "Raspbmc":
            for key in ("sys.xbmc.res","sys.xbmc.ae","sys.xbmc.shut","remote.gpio.enable","remote.gpio.profile", "sys.xbmc.headers", "sys.xbmc.sc"):
                exec "dict_switches[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
            if __settings__.getSetting("sys.config.freq.manual") == "true":
                for key in ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt","sys.config.freq.isp"):
                    exec "dict_sys[\"%s\"]=float2int(__settings__.getSetting(\"%s\"))" % (key,key)

            for key in ("sys.config.decode.mpg2","sys.config.decode.wvc1","sys.config.decode.dts","sys.config.decode.ac3"):
                exec "dict_sys[\"%s\"]=__settings__.getSetting(\"%s\")" % (key,key)
            if __settings__.getSetting("sys.config.disable.overscan") == "true":
                dict_sys["sys.config.disable.overscan"]="1"
            else:
                dict_sys["sys.config.disable.overscan"]="0"

            if __settings__.getSetting("sys.config.freq.manual") == "false":
                init_value={"sys.config.freq.arm":800,"sys.config.freq.core":250,"sys.config.freq.gpu":250,"sys.config.freq.isp":250,"sys.config.freq.sdram":400,"sys.config.freq.overvolt":0}
                if __settings__.getSetting("sys.config.freq.profile") == "0":
                    dict_sys["sys.config.freq.arm"]=850
		    dict_sys["sys.config.freq.core"]=375
                    for key in ("sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt","sys.config.freq.isp"):
                        exec "dict_sys[\"%s\"]=init_value[\"%s\"]" % (key,key)
                if __settings__.getSetting("sys.config.freq.profile") == "1":
                    dict_sys["sys.config.freq.arm"]=900
                    dict_sys["sys.config.freq.core"]=375
                    for key in ("sys.config.freq.gpu", "sys.config.freq.sdram","sys.config.freq.overvolt","sys.config.freq.isp"):
                        exec "dict_sys[\"%s\"]=init_value[\"%s\"]" % (key,key)
                if __settings__.getSetting("sys.config.freq.profile") == "2":
                    dict_sys["sys.config.freq.arm"]=950
                    dict_sys["sys.config.freq.core"]=450
                    dict_sys["sys.config.freq.sdram"]=450
                    dict_sys["sys.config.freq.isp"]=450
                    dict_sys["sys.config.freq.overvolt"]=6
                    dict_sys["sys.config.freq.gpu"]=250

            for value in  __settings__.getSetting("sys.config.addition").split(";"):
                if len(value) >0:
                    item=value.split("=")[0].strip()
                    key=value.split("=")[1].strip()
                    dict_sys[item]=key

#        if dict_nm["nm.dhcp"] == "true":
#             for key in ("nm.address","nm.netmask","nm.gateway","nm.dns","nm.search"):
#                 exec "del dict_nm[\"%s\"]" % (key)
        return dict_nm,dict_sys,dict_service,dict_switches

def load_sysconfig(settings=None):
    f=open('/boot/config.txt','r')
    ini_str = '[root]\n' + f.read()
    ini_fp = StringIO.StringIO(ini_str)
    file_config = ConfigParser.RawConfigParser()
    file_config.readfp(ini_fp)
    config={}
    if settings != None:
        for item in settings.items():
            if not item[0].startswith("sys.config."):
                config[item[0]] = ""
    init_value={"sys.config.freq.arm":800,"sys.config.freq.core":250,"sys.config.freq.gpu":250,"sys.config.freq.isp":250,"sys.config.freq.sdram":400,"sys.config.freq.overvolt":0}
    for key in ("sys.config.freq.arm","sys.config.freq.core","sys.config.freq.gpu","sys.config.freq.sdram","sys.config.freq.overvolt","sys.config.freq.isp"):
        exec "config[\"%s\"]=init_value[\"%s\"]" % (key,key)
    config["sys.config.disable.overscan"] = "1"
    config["sys.config.decode.mpg2"] = ""
    config["sys.config.decode.wvc1"] = ""
    config["sys.config.decode.dts"] = ""
    config["sys.config.decode.ac3"] = ""
    for item in config.items():
        if not item[0].startswith("sys.config."):
            try:
                config[item[0]] = file_config.get("root",item[0])
            except:
                pass
    try:
        config["sys.config.freq.arm"] = int(file_config.get("root","arm_freq"))
    except:
        pass
    try:
        config["sys.config.freq.core"]  = int(file_config.get("root","core_freq"))
    except:
        pass
    try:
        config["sys.config.freq.isp"]  = int(file_config.get("root","isp_freq"))
    except:
        pass
    try:
        config["sys.config.freq.gpu"] =  int(file_config.get("root","gpu_freq"))
    except:
        pass
    try:
        config["sys.config.freq.sdram"] =  int(file_config.get("root","sdram_freq"))
    except:
        pass
    try:
        config["sys.config.freq.overvolt"] =  int(file_config.get("root","over_voltage"))
    except:
        pass
    try:
        config["sys.config.disable.overscan"] =  file_config.get("root","disable_overscan")
    except:
        pass
    try:
        config["sys.config.decode.mpg2"]  =  file_config.get("root","decode_MPG2")
    except:
        pass
    try:
        config["sys.config.decode.wvc1"] =   file_config.get("root","decode_WVC1")
    except:
        pass
    try:
        config["sys.config.decode.dts"]  = file_config.get("root","decode_DTS")
    except:
        pass
    try:
        config["sys.config.decode.ac3"] =  file_config.get("root","decode_DDP")
    except:
        pass
    f.close()
    return config

def set_sysconfig(config,time_stamp):
    file_config = ConfigParser.RawConfigParser()
    file_config.optionxform = str
    file_config.add_section('root')
    import xbmc,os
    xbmc.log(str(config))
    for item in config.items():
        if not item[0].startswith("sys.config."):
            file_config.set('root',item[0],item[1])
    if config["sys.config.freq.arm"] != 700:
        file_config.set('root','arm_freq',config["sys.config.freq.arm"] )
    if config["sys.config.freq.core"] != 250:
        file_config.set('root','core_freq',config["sys.config.freq.core"] )
    if config["sys.config.freq.gpu"] !=250:
        file_config.set('root','gpu_freq',config["sys.config.freq.gpu"] )
    if config["sys.config.freq.isp"] !=250:
        file_config.set('root','isp_freq',config["sys.config.freq.isp"] )
    if config["sys.config.freq.sdram"] != 400:
        file_config.set('root','sdram_freq',config["sys.config.freq.sdram"] )
    if config["sys.config.freq.overvolt"] != 0:
        file_config.set('root','over_voltage',config["sys.config.freq.overvolt"] )
    else:
        file_config.set('root','force_turbo','1' )

    file_config.set('root','disable_overscan',config["sys.config.disable.overscan"] )

    if config["sys.config.decode.mpg2"] != "":
        file_config.set('root','decode_MPG2',config["sys.config.decode.mpg2"] )
    if config["sys.config.decode.wvc1"]  != "":
        file_config.set('root','decode_WVC1',config["sys.config.decode.wvc1"] )
    if config["sys.config.decode.dts"]  != "":
        file_config.set('root','decode_DTS',config["sys.config.decode.dts"] )
    if config["sys.config.decode.ac3"] != "":
        file_config.set('root','decode_DDP',config["sys.config.decode.ac3"] )
    file_config.set('root','gpu_mem_512','128')
    file_config.set('root','gpu_mem_256','112')
    file_config.set('root', 'start_file', 'start_x.elf')
    file_config.set('root', 'fixup_file', 'fixup_x.dat')
    file_config.set('root', 'hdmi_ignore_cec_init', '1')
    HOME=os.getenv('HOME')
    os.system("mkdir -p "+HOME+"/.xbmc/userdata/addon_data/script.raspbmc.settings")
    f=open(HOME+'/.xbmc/userdata/addon_data/script.raspbmc.settings/config.txt-'+time_stamp,'w')
    ini_str = ''
    ini_fp = StringIO.StringIO(ini_str)
    file_config.write(ini_fp)
    ini_fp.seek(7)
    for line in ini_fp.readlines():
        xbmc.log(str(line.replace(" = ","=")))
        f.write(line.replace(" = ","="))
    f.close()
    os.system("sudo cp "+HOME+"/.xbmc/userdata/addon_data/script.raspbmc.settings/config.txt-"+time_stamp+" "+"/boot/config.txt")


def enable_disable_service(service,state):
    import os
    import xbmc
    if state:
	if service == "samba" or service == "ssh" or service == "ftp":
		os.system("sudo /scripts/xinet.sh 'enable' '" + service + "'")
		os.system("sudo /sbin/initctl stop xinetd")
                os.system("sudo /sbin/initctl start xinetd")
	else:
        	os.system("sudo /sbin/initctl emit --no-wait enable-"+service)
        xbmc.log("enable service: " +service)
    if not state:
	if service == "samba" or service == "ssh" or service == "ftp":
		os.system("sudo /scripts/xinet.sh 'disable' '" + service + "'")
		os.system("sudo /sbin/initctl stop xinetd") 
                os.system("sudo /sbin/initctl start xinetd")
	else:
		os.system("sudo /sbin/initctl emit --no-wait disable-"+service)
        xbmc.log("disable service: " +service)




def set_services(services):
    config_file_dict={"sys.service.ftp":"ftp.conf","sys.service.ssh":"ssh.conf","sys.service.samba":"samba.conf","sys.service.xinetd":"xinetd.conf", "sys.service.remote":"eventlircd.conf","sys.service.avahi":"avahi-daemon.conf","sys.service.cron":"cron.conf",
                      "sys.service.nfs":"gssd.conf,idmapd.conf,portmap.conf,portmap-boot.conf,portmap-wait.conf,rpcbind-boot.conf,statd.conf",
                      "sys.service.tvh":"tvheadend.conf", "sys.service.boblight":"boblight.conf", "sys.service.surveil":"surveil.conf", "sys.service.vnc":"vnc.conf", "sys.service.sab":"sabnzbd.conf", "sys.service.del": "deluge.conf"}
    for service in services.items():
        service_state = None
        if service[1] == "false":
            service_state = False
        if service[1] == "true":
            service_state = True
        if service_state != None:
            for file_name in config_file_dict[service[0]].split(","):
                name = file_name.replace(".conf","")
                enable_disable_service(name,service_state)

