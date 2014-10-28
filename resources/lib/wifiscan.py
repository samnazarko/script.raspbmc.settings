# declare file encoding
# -*- coding: utf-8 -*-

#  Copyright (C) 2013 Sam Nazarko
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

import xbmcgui
import os
import sys
import xbmc
import traceback
import string
from exception_handling import *

class Wrapped(object):
    def __init__(self, file_,dp):
        self._file = file_
        self._oldread = 0
        self._totalread = 0
        self._size = os.fstat(file_.fileno()).st_size
        self._dp = dp

    def read(self,size):
        self._totalread += size
        if self._totalread - self._oldread >= self._size/100:
           self._dp.update(self._totalread *100/self._size)
           self._oldread = self._totalread
        return self._file.read(size)

    def __getattr__(self, attr):#
        return getattr(self._file, attr)

def scannet():
    dialog = xbmcgui.Dialog()
    wifi_list = networks=string.split(os.popen("bash /scripts/scan-networks.sh").read(),"\n")
    wifi_list.pop()    
    if wifi_list == -9:
		# No wireless detected
		dialog.ok("WiFi configuration", "No wireless networks were detected!\nPlease check your adapter.")
    else:
		answer = dialog.select("Please select a WiFi network", wifi_list)
		if answer < 0 or answer >= len(wifi_list):
			return -9
    # set this as the network and relaunch RMC settings
    import xbmcaddon
    __settings__ = xbmcaddon.Addon()
    __settings__.setSetting("nm.wifi.ssid",wifi_list[answer])
    __settings__.setSetting("nm.mode", "1")    
    dialog.ok("WiFi configuration", "Wifi Hotspot " + wifi_list[answer] + " is selected.\nPlease configure remaining wireless settings") 
