#  Exception Handling inspired by buggalo,  Tommy Winther, http://tommy.winther.nu
#
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

import datetime
import os
import platform
import sys
import traceback
import xbmc
import xbmcaddon
import xbmcgui
import types
import subprocess
import StringIO

def gatherData(type, value, tracebackInfo, extraData):
    data = dict()
    data['version'] = 4
    data['timestamp'] = datetime.datetime.now().isoformat()

    exception = dict()
    exception['stacktrace'] = traceback.format_tb(tracebackInfo)
    exception['type'] = str(type)
    exception['value'] = str(value)
    data['exception'] = exception

    system = dict()
    try:
        if hasattr(os, 'uname'):
            # Works on recent unix flavors
            (sysname, nodename, release, version, machine) = os.uname()
        else:
            # Works on Windows (and others?)
            (sysname, nodename, release, version, machine, processor) = platform.uname()

        system['nodename'] = nodename
        system['sysname'] = sysname
        system['release'] = release
        system['version'] = version
        system['machine'] = machine
    except Exception, ex:
        system['sysname'] = sys.platform
        system['exception'] = str(ex)
    data['system'] = system

    addon = xbmcaddon.Addon()
    addonInfo = dict()
    addonInfo['id'] = addon.getAddonInfo('id')
    addonInfo['name'] = addon.getAddonInfo('name')
    addonInfo['version'] = addon.getAddonInfo('version')
    addonInfo['path'] = addon.getAddonInfo('path')
    addonInfo['profile'] = addon.getAddonInfo('profile')
    data['addon'] = addonInfo

    xbmcInfo = dict()
    xbmcInfo['buildVersion'] = xbmc.getInfoLabel('System.BuildVersion')
    xbmcInfo['buildDate'] = xbmc.getInfoLabel('System.BuildDate')
    xbmcInfo['skin'] = xbmc.getSkinDir()
    xbmcInfo['language'] = xbmc.getInfoLabel('System.Language')
    data['xbmc'] = xbmcInfo

    execution = dict()
    execution['python'] = sys.version
    execution['sys.argv'] = sys.argv
    data['execution'] = execution


    extraDataInfo = dict()
    try:

        if isinstance(extraData, dict):
            for (key, value) in extraData.items():
                if isinstance(extraData, str):
                    extraDataInfo[key] = value.decode('utf-8', 'ignore')
                elif isinstance(extraData, unicode):
                    extraDataInfo[key] = value
                else:
                    extraDataInfo[key] = str(value)
        elif extraData is not None:
            extraDataInfo[''] = str(extraData)
    except Exception, ex:
        (type, value, tb) = sys.exc_info()
        traceback.print_exception(type, value, tb)
        extraDataInfo['exception'] = str(ex)
    data['extraData'] = extraDataInfo

    return data


def onExceptionRaised(extraData = None):
    """
    Invoke this method in an except clause to allow the user to submit
    a bug report with stacktrace, system information, etc.

    This also avoids the 'Script error' popup in XBMC, unless of course
    an exception is thrown in this code :-)

    @param extraData: str or dict
    """
    # start by logging the usual info to stderr
    (type, value, traceback) = sys.exc_info()
    import traceback as tb
    tb.print_exception(type, value, traceback)

#    try:
#        # signal error to XBMC to hide progress dialog
#        HANDLE = int(sys.argv[1])
#        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
#    except Exception:
#        pass

    heading = "Script Error Detected"
    data = gatherData(type, value, traceback, extraData)
    for key in ("exception","timestamp", "system","version","execution","xbmc","addon"):
        exec "data_%s = data[\"%s\"]" % (key,key)
    message="script error report filed on "+str(data_timestamp)+"\n\n"
    message=message+"==========[Addon]\n"
    for sub_key in ("id","name","version","path","profile"):
        if sub_key != "id":
            message=message+sub_key.title()+"\t\t\t "+str(data_addon[sub_key])+"\n"
        else:
            message=message+"ID"+"\t\t\t "+str(data_addon[sub_key])+"\n"
    message=message+"\n\n"
    message=message+"==========[Exception]\n"
    for sub_key in ("type","value","stacktrace"):
        if isinstance(data_exception[sub_key], types.ListType):
            message=message+sub_key.title()+"\t\t\t "+str(",".join(data_exception[sub_key])).replace("\n","\n\t\t\t").strip()+"\n"
        else:
            message=message+sub_key.title()+"\t\t\t "+str(data_exception[sub_key])+"\n"
    message=message+"\n\n"
    message=message+"==========[Execution]\n"
    sub_key = "python"
    message=message+sub_key.title()+"\t\t\t "+str(data_execution[sub_key]).replace("\n"," ")+"\n"
    sub_key = "sys.argv"
    message=message+sub_key+"\t\t\t "+str(",".join(data_execution[sub_key]))+"\n"

    message=message+"\n\n"
    message=message+"==========[System]\n"
    for sub_key in ("nodename","sysname","release","version","machine"):
        message=message+sub_key.title()+"\t\t\t "+str(data_system[sub_key])+"\n"
    message=message+"\n\n"
    message=message+"==========[XBMC]\n"
    for sub_key in ("buildVersion","buildDate","language","skin"):
        if sub_key.startswith("build"):
            keyword=sub_key.replace("build","")
            message=message+"Build "+keyword+"\t\t\t "+str(data_xbmc[sub_key])+"\n"
        else:
            message=message+sub_key.title()+"\t\t\t "+str(data_xbmc[sub_key])+"\n"
    message=message+"\n\n"
    message=message+"==========[net devices]\n"
    f=open("/proc/net/dev","r")
    for line in f.readlines():
        message=message+line
    f.close()
    message=message+"\n\n"
    message=message+"==========[ifconfig]\n"
    command=("ifconfig")
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    process.wait()
    for line in process.stdout:
        message=message+line
    xbmc.log(message,xbmc.LOGERROR)
    f=open("/var/log/syslog",'r')
    f.seek(-102400, 2)
    data_syslog=f.read(102400)
    f.close()
    fp = StringIO.StringIO(data_syslog)
    l=fp.readlines()
    fp.close()
    l.reverse()
    p=[]
    for line in l:
        p.append(line)
        if "Linux version" in line:
            break
    p.reverse()
    message=message+"\n\n"
    message=message+"==========[syslog]\n"
    for line in p:
        message=message+line

    #xbmc.log(''.join('!! ' + line for line in str(data)),xbmc.LOGERROR)
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno('Script Error', 'A script error is detected', 'Do you want to file an anonymous report via pastebin?')
    if ret:
        from pastebin import *
        pastebin_link=paste_data(message)
        if pastebin_link != None:
            dialog.ok('Script Error Report','A script error report was successfully submitted', 'Plase go to http://forum.stmlabs.com with the following info',pastebin_link)
        else:
            dialog.ok('Script Error Report','A script error report was not successfully submitted', 'Plase submit error report manually to http://forum.stmlabs.com')
    sys.exit(0)



def onNoNetworkInterfaceFoundRaised():
    """
    Invoke this method in an except clause to allow the user to submit
    a bug report with stacktrace, system information, etc.

    This also avoids the 'Script error' popup in XBMC, unless of course
    an exception is thrown in this code :-)

    @param extraData: str or dict
    """


#    try:
#        # signal error to XBMC to hide progress dialog
#        HANDLE = int(sys.argv[1])
#        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
#    except Exception:
#        pass
    message="No Active Network Interface found"
    message=message+"\n\n"
    message=message+"==========[net devices]\n"
    f=open("/proc/net/dev","r")
    for line in f.readlines():
        message=message+line
    f.close()
    message=message+"\n\n"
    message=message+"==========[ifconfig]\n"
    command=("ifconfig")
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    process.wait()
    for line in process.stdout:
        message=message+line
    xbmc.log(message,xbmc.LOGERROR)
    f=open("/var/log/syslog",'r')
    f.seek(-102400, 2)
    data_syslog=f.read(102400)
    f.close()
    fp = StringIO.StringIO(data_syslog)
    l=fp.readlines()
    fp.close()
    l.reverse()
    p=[]
    for line in l:
        p.append(line)
        if "Linux version" in line:
            break
    p.reverse()
    message=message+"\n\n"
    message=message+"==========[syslog]\n"
    for line in p:
        message=message+line

    xbmc.log(''.join('!! ' + line for line in str(data)),xbmc.LOGERROR)
    xbmc.executebuiltin('XBMC.Notification('+'"No suitable network/interface found", "Not all settings will work. Check you connection and try again.",5000,"'+'")')
