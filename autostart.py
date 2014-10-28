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
import pwd
import requests
#import xbmc
#import traceback

# addon constants
__author__ = "s7mx1"
__url__ = "http://www.raspbmc.com"
__svn_url__ = ""
__credits__ = "Raspbmc plugin written and maintained by s7mx1"

# reload(sys)
# sys.setdefaultencoding('utf-8')

def sortedDict(adict):
	items = adict.items()
	items.sort()
	bdict={}
	for key,value in items:
		bdict[key]=value
	return bdict

def check_service_running(service):
	import dbus
	bus = dbus.SystemBus()
	upstart = bus.get_object("com.ubuntu.Upstart", "/com/ubuntu/Upstart")
	try:
		path = upstart.GetJobByName(service, dbus_interface="com.ubuntu.Upstart0_6")
		job = bus.get_object("com.ubuntu.Upstart", path)
		path = job.GetInstance([], dbus_interface="com.ubuntu.Upstart0_6.Job")
		instance = bus.get_object("com.ubuntu.Upstart", path)
		props = instance.GetAll("com.ubuntu.Upstart0_6.Instance", dbus_interface=dbus.PROPERTIES_IFACE)
		if props["state"] == "running":
			return "false"
		elif props["state"] == "stopped":
			return "true"
	except:
		return "true"

if ( __name__ == "__main__" ):
	
	import xbmcaddon
	__settings__ = xbmcaddon.Addon()
	__version__    = __settings__.getAddonInfo('version')
	__cwd__        = __settings__.getAddonInfo('path')
	__firstrun__   = __settings__.getSetting("firstrun")
	BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
	sys.path.append (BASE_RESOURCE_PATH)
	DISTRO = "Raspbmc"
	USER=pwd.getpwuid(1000)[0]

	if USER == "pi":
		__addon__ = "scrip.raspbmc.settings"
		DISTRO = "Raspbmc"
	if USER == "atv":
		__addon__ = "scrip.crystalbuntu.settings"
		DISTRO = "Crystalbuntu"
	sys.path.append ('/scripts')
	from power import *

	lirc_workaround("Start")        

	try:
		if os.path.isdir("/var/run/xbmc"):
			os.system('sudo /sbin/initctl emit --no-wait xbmc-started FIRST_RUN=no')
		else:
			os.system('sudo /sbin/initctl emit --no-wait xbmc-started FIRST_RUN=yes')
			os.system('sudo mkdir /var/run/xbmc')
		os.system('logger -t xbmc "xbmc started"')
		if not os.path.isfile("/bin/fbset") and DISTRO == "Raspbmc":
			os.system("echo '\\0033\\0143' > /dev/tty1")
			os.system("echo '\\033[?17;0;0c' > /dev/tty1")
			os.system('echo "4 1 1 7" | sudo tee /proc/sys/kernel/printk')
	except:
		pass

	from sys_config import *
	import xbmc
	network_settings, system_settings, service_settings, switch_settings=load_settings(__settings__,DISTRO)
	services={}
	for item in service_settings.items():
		services[item[0]]=service_settings[item[0]]
	services["sys.service.avahi"]="true"
	xbmc.log("services: " +str(services))
	set_services(services)

	from nm_util import *
	nm = NetworkManager()
	try:
		nic_list  = display_connection(nm)
		nic_to_configure=nic_list[0]
		for nic in nic_list:
			if nic.get('type') == '802-3-ethernet':
				nic_to_configure=nic
				break
		if len(nic_to_configure['address']) > 0:
			xbmc.executebuiltin('XBMC.Notification('+'"'+DISTRO+': Active Network Detected", "IP:   '+nic_to_configure['address']+'",10000,"'+'")')
	except:
		pass

	if __settings__.getSetting("firewall.disable") == "true":
		os.system('sudo iptables -F;sudo iptables -X;sudo iptables -t nat -F;sudo iptables -t nat -X;sudo iptables -t mangle -F;sudo iptables -t mangle -X;sudo iptables -P INPUT ACCEPT;sudo iptables -P FORWARD ACCEPT;sudo iptables -P OUTPUT ACCEPT')

	if __settings__.getSetting("remote.gpio.enable") == "true" and DISTRO == "Raspbmc":
		os.system('test x"`grep lirc_rpi /proc/modules`" != "x" || sudo modprobe lirc_rpi')

	import xbmcgui
	dialog = xbmcgui.Dialog()
	
	if DISTRO == "Raspbmc" and os.path.isfile("/home/pi/.bootstatus") and check_service_running("wd") == "true" and not os.path.isfile("/home/pi/.nowarning"):
		dialog.ok("Raspbmc did not shut down properly", "Raspbmc should always be shut down via the\npower icon in the lower left corner")
		dialog.ok("Raspbmc did not shut down properly", "If your device keeps freezing or rebooting\nvisit www.raspbmc.com/power for advice")
	
	if DISTRO == "Raspbmc":
		os.system('sudo /sbin/initctl emit --no-wait start-wd')

	if __firstrun__ == "false" and os.path.isfile("/boot/config.txt") and  DISTRO == "Raspbmc":
		#xbmc.log("system settings from addon: " + str(system_settings))
		config=load_sysconfig(settings=system_settings)
		#xbmc.log("system settings from addon: " + str(system_settings))
		config=sortedDict(config)
		system_settings = sortedDict(system_settings)
		xbmc.log("system settings from addon: " + str(system_settings))
		xbmc.log("system settings from /boot/config.txt: " +str(config))

	if __firstrun__ == "true":
		from select_language import *
		select_language(__cwd__)

	# __firstrun__ = ''	# this is needed for my laptop to test the addon
	# __settings__.setSetting("OSMCmessage1", 'true')
	# __settings__.setSetting("OSMCmessage2", 'true')

	OSMCmessage1 = __settings__.getSetting("OSMCmessage1")
	OSMCmessage2 = __settings__.getSetting("OSMCmessage2")

	if __firstrun__ != "true":

		if OSMCmessage1 == 'true':

			__settings__.setSetting("OSMCmessage1", 'false')

			dialog.ok('RaspBMC is becoming OSMC', 'OSMC is a multiplatform yada yada', 'more osmc stuff')

			response = dialog.yesno('RaspBMC is becoming OSMC',
									'OSMC will be on Kickstarter.',
									'Do you want to follow OSMC on KickStarter?',
									nolabel="No thanks.",
									yeslabel="Enter email")

			if response:
				email_address = dialog.input('Follow OSMC on KickStarter')
				if '@' in email_address:
					
					print 'do stuff here'


		elif OSMCmessage2 == 'true':

			__settings__.setSetting("OSMCmessage2", 'false')

			# check url
			url = 'http://getvero.tv/SHOW_MSG'
			r = requests.head(url)
			code = r.status_code
			if code not in [404, '404']:

				response = dialog.ok("Vero is now available!",
									"We are now taking orders for Vero.",
									"Visit XYZ to find out more." )




