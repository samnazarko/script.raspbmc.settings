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

import urllib2
import re
import xbmcgui
import os
import sys
import xbmc
import traceback
import httplib
import urlparse
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

def error_logging():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback) 
    xbmc.log(''.join('!! ' + line for line in lines))

parse_re = re.compile('href="([^"]*)".*(..-...-.... ..:..).*?(\d+[^\s<]*|-)')
def list_apache_dir(url,file):
    list=[]
    new_url = ""
    if not url.endswith('/'):
        url += '/'
    try:
        o=urlparse.urlparse(url)
        conn = httplib.HTTPConnection(o.netloc)
        conn.request("HEAD", "/index.html")
        res = conn.getresponse()
        new_url = res.getheader('location').replace("/index.html","")+o.path
        if len(new_url) >0:
            url = new_url
        html = urllib2.urlopen(url+file).readlines()
    except urllib2.URLError, e:
        error_logging()
        error = -1
        return list,error,new_url
    if len(html) >0:
        for line in html:
            list.append(line.rstrip())
            list.append(line.split(".")[0]+".md5")
    else:
        error = -1
        return list,error,new_url
    return list,0,new_url


## downloader with a progress bar
def Downloader(url,dest,description,heading):
    dp = xbmcgui.DialogProgress()
    dp.create(heading,description)
    dp.update(0)
    
    # Remove old file when present
    if os.path.isfile(dest):
        os.remove(dest)
        
    try:
        old_percent=0
        
        # Init download
        u = urllib2.urlopen(url)            
        
        # Open file for writing
        f = open(dest,'wb')
        
        # Calculate the download total length
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        file_size_dl = 0
        block_sz = 8192
        
        # Download it, update progress every block_sz bytes
        while True:
        
            buffer = u.read(block_sz)
            
            # Download finished
            if not buffer:
                break
            
            file_size_dl += len(buffer)
            f.write(buffer)
            percent = file_size_dl * 100 / file_size
            
            # Update percentage only when needed (faster, dialog update is slow)
            if int(percent) - int(old_percent) >= 1:
                dp.update(percent)
                old_percent=percent
            
            # Check if the download was cancelled
            if (dp.iscanceled()):
                dp.close()
                return -9
                break
        
        dp.update(100)
        f.close()
        return 0
    except urllib2.URLError, e:
        xbmc.log("Failed to download nightly release. Error: %s" % (e.reason))
        error_logging()
        return -1
    except urllib2.HTTPError, e:
        xbmc.log("Failed to download nightly release. Error: %s" % (e.code))
        error_logging()
        return -1
    except KeyboardInterrupt,SystemExit:
        dp.close()
        return -9



def md5(fileName,dp):
    """Compute md5 hash of the specified file"""
    #import xbmc
    filesize=os.path.getsize(fileName)
    try:
        import hashlib
        m = hashlib.md5()
    except:
        import md5
        m = md5.new()
    try:
        fd = open(fileName,"rb")
    except IOError:
        error_logging()
        return "IOError"
    old_progress=0
    count =0
    while True:
        d = fd.read(8096)
        if not d:
            break
        m.update(d)
        count += 1
        progress = (count * 809600)/filesize
        if progress - old_progress >= 1:
            dp.update(progress)
            old_progress = progress
    fd.close()
    dp.update(100)
    return m.hexdigest()

def upgrade(url,path):
    import tarfile
    error = -1
    file_list, error, location = list_apache_dir(url,"available")
    if len(location) >0:
        url = location
    if error == 0:
        version_list=[]
    else:
        return error

    for file in file_list:
        if len(file.split(".")[0]) > 0:
            if file.split(".")[0] not in version_list:
                version_list.append(file.split(".")[0])
    version_list.sort()
    version_list.reverse()
    dialog = xbmcgui.Dialog()
    answer =dialog.select("List of xbmc nightlies", version_list)
    if answer < 0 or answer >= len(version_list):
        return -9
    version=version_list[answer]
    new_list=[]
    for file in file_list:
        if file.split(".")[0] == version:
            new_list.append(file)
            error = Downloader(url+file,os.path.join(path,file),"Downloading "+file, "Fetching upgrade")
            if error != 0:
                return  error
    file_list = new_list
    dp = xbmcgui.DialogProgress()
    dp.create("Verifying", "XBMC nightly","Verifying upgrade package")
    dp.update(0)
    new_list = []
    for file in file_list:
        if file.endswith(".md5"):
            expect_md5=open(os.path.join(path,file),'r').readline().split()[0]
            xbmc.log("md5sum for  %s repository is %s" % (version,expect_md5))
        else:
            new_list.append(file)
            file_md5 = md5(os.path.join(path,file),dp)
            xbmc.log("md5sum for  downloaded %s is %s" % (version,file_md5))
    if file_md5 != expect_md5:
        dp.close()
        error = -2
        return error
    else:
        dp.update(100)
        file = new_list[0]
        xbmc.log("File name %s to extract" % file)
        dp.create("Extracting","XBMC nightly", "Extracting upgrade package")
        dp.update(0)
        dest_path = os.path.join(path,version)
        upgrade_file = Wrapped(open(os.path.join(path,file)),dp)
        try:
            tar = tarfile.open(fileobj=upgrade_file)
            tar.extractall(path=dest_path)
            tar.close()
            dp.update(100)
            dp.close()
        except KeyboardInterrupt,SystemExit:
            tar.close()
            dp.close()
            return -9
        except:
            tar.close()
            dp.close()
            error = -3
            error_logging()
            return error
        try:
            dst=os.path.join(os.getenv("HOME"),".xbmc-current")
            src=os.path.join(path,version,"xbmc-bcm")
            if os.path.exists(dst):
                os.remove(dst)
            os.symlink(src, dst)
            result=dialog.yesno(version, "XBMC is now setup to use "+version, "Please select \"Yes\" to reload xbmc, otherwise choose \"No\".")
            if result:
                xbmc.executebuiltin('Quit')
        except:
            onExceptionRaised()
        return 0

def reset(url,dest):
    os.system("sudo umount /boot")
    error = Downloader(url,dest,"Downloading", "Downloading factory reset image")
    if error == 0:
        dp = xbmcgui.DialogProgress()
        dp.create("Factory Reset","Preparing", "One moment please")
        dp.update(0)
        os.system("gunzip -c "+dest+" | sudo dd of=/dev/mmcblk0 conv=fdatasync")
        dp.update(100,"Factory Reset Image Installed")
        dp.close()
        dialog = xbmcgui.Dialog()
        result=dialog.yesno("Factory Reset", "Factory reset ready", "Would you like to begin restoration now? ")
        if result:
            if os.path.isfile("/proc/sys/kernel/sysrq"):
                os.system("echo 1 | sudo tee /proc/sys/kernel/sysrq")
                os.system("echo b | sudo tee /proc/sysrq-trigger")
            else:
                xbmc.executebuiltin('Reboot')
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok("Error %s" % error, "Downloading restore image failed with error code: "+str(error), "Please try it again")


def switch(path):
    selection_list = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path,item)):
            selection_list.append(item)
    selection_list.sort()
    selection_list.reverse()
    selection_list.append("xbmc release")
    dialog = xbmcgui.Dialog()
    answer =dialog.select("List of installed XBMC(s)", selection_list)
    if answer <0 or answer >=len(selection_list):
        return -9
    version=selection_list[answer]
    dst=os.path.join(os.getenv("HOME"),".xbmc-current")
    if version != "xbmc release":
        src=os.path.join(path,version,"xbmc-bcm")
    else:
        src="/opt/xbmc-bcm"
    if os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)
    result=dialog.yesno(version, "XBMC is now setup to use "+version, "Please select \"Yes\" to reload xbmc, otherwise choose \"No\".")
    if result:
        xbmc.executebuiltin('Quit')

def delete(path):
    selection_list = []
    dst=os.path.join(os.getenv("HOME"),".xbmc-current")
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path,item)) and os.path.join(path,item,"xbmc-bcm") != os.path.realpath(dst):
            selection_list.append(item)
    selection_list.sort()
    selection_list.reverse()
    dialog = xbmcgui.Dialog()
    answer =dialog.select("List of installed nightlies", selection_list)
    if answer <0 or answer >=len(selection_list):
        return -9
    version=selection_list[answer]
    src=os.path.join(path,version)
    if os.path.exists(src):
        os.system("rm -rf " + src)
        dialog.ok("Nightly deleted","%s deleted." % (version))

def error_handling(error):
    dialog = xbmcgui.Dialog()
    message1= "error code %s" % (error)
    message2= ""
    if error == -1:
        message1="Problem connecting to nightly server. "
        message2="Please check network connections and try it again later."
    if error == -2:
        message1="Download upgrade failed at varification. Corrupted download? "
        message2="Please check network connections, verify sd card and try it again later."
    if error == -3:
        message1="Extraction of upgrade packages failed."
        message2="Please clean ~/.upgrade folder and try it again later."
    if error == -4:
        message1="Passwords do not match"
        message2="Please enter passwords again."
    if error == -5:
        message1="Passwords not set"
        message2="Please enter passwords again."
    if error == -6:
        message1="Setting password failed"
        message2="Please try again later."
    if error == -9:
        message1="User cancelled"
        message2="Please try again later."
    if error != 0:
        dialog.ok("Error %s" % error, message1, message2)

def set_password(settings):
    password1 = settings.getSetting("sys.password")
    password2 = settings.getSetting("sys.password_confirm")

    if password1 != password2:
        error = -4
        return error
    else:
        if len(password1) == 0:
            error = -5
        else:
            try:
                import pexpect
                passwd = pexpect.spawn("sudo /usr/bin/passwd pi")
                for repeat in (1, 2):
                    passwd.expect("password: ")
                    passwd.sendline(password1)
                    xbmc.sleep(100)
                dialog = xbmcgui.Dialog()
                dialog.ok("Password updated", "Password updated successfully")
                settings.setSetting("sys.password","")
                settings.setSetting("sys.password_confirm","")
                return 0
            except:
                settings.setSetting("sys.password","")
                settings.setSetting("sys.password_confirm","")
                onExceptionRaised()
                error = -6
                return error

