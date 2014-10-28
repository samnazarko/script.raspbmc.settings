# declare file encoding 
# -*- coding: utf-8 -*-

#  Copyright (C) 2013 S7MX1
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
import xbmc
import xbmcgui


        
def get_language_list(__cwd__):
    list = []
    path = os.path.join(__cwd__,'resources','language')
    for dirname in os.listdir(path):
        xbmc.log(dirname)
        if len(dirname) >0:
            xbmc.log('found language: '+dirname)
            list.append(dirname)
    list.sort()
    return list

def read_xml_entry(XML,element,entry):
    import xml.etree.ElementTree as ET
    if os.path.isfile(XML):
        tree = ET.parse(XML)
        root = tree.getroot()
        for child in root:
            if child.tag == element:
                for subchild in child:
                    if subchild.tag == entry:
                        return subchild.text

def write_xml_entry(XML,element,entry,value):
    import xml.etree.ElementTree as ET
    if os.path.isfile(XML):
        tree = ET.parse(XML)
        root = tree.getroot()
        for child in root:
            if child.tag == element:
                for subchild in child:
                    if subchild.tag == entry:
                        subchild.text = value
        tree.write(XML)

def get_string_list(__cwd__,lan_list,id):
    import xml.etree.ElementTree as ET
    list = []
    list1 = []
    for language in lan_list:
        xbmc.log("found language: "+language)
        name = 'welcome.xml'
        file = os.path.join(__cwd__,'resources','language',language,name)
        if os.path.isfile(file):
            try:
                tree = ET.parse(file)
            except:
                xbmc.log("something wrong with the "+file+ " file")
            try:
                for element in tree.getiterator('string'):
                    if element.get('id') == str(id):
                        xbmc.log("string: "+element.text)
                        list.append(language)
                        list1.append(element.text)
            except:
                xbmc.log("cannot get string id in "+file+ " file")
        else:
            xbmc.log("deleting "+language+" from language list")
    return list,list1
    
    

def set_lan(language):
    gui_xml=os.path.join(xbmc.translatePath("special://userdata"),"guisettings.xml")
    language_current = read_xml_entry(gui_xml,"locale","language")
    if language != language_current:
        xbmc.log("I will try to set the language to "+language)
        write_xml_entry(gui_xml,"locale","language",language)
        xbmc.log("language: "+read_xml_entry(gui_xml,"locale","language"))
        xbmc.log("country: "+read_xml_entry(gui_xml,"locale","country"))
        return True
    else:
        return False


def set_font_arial():
    gui_xml=os.path.join(xbmc.translatePath("special://userdata"),"guisettings.xml")
    font = 'Arial'
    font_current = read_xml_entry(gui_xml,"lookandfeel","font")
    if font != font_current:
            print "set fonts to ", font
            write_xml_entry(gui_xml,"lookandfeel","font",font)
            xbmc.log("set to font "+ font+ "successfully")
            xbmc.log("reload skin so new font will take effect")
            xbmc.sleep(500)
            xbmc.executebuiltin('ReloadSkin()')


def select_language(__cwd__):
    wizard_file = os.path.join(xbmc.translatePath("special://home"),'wizard')
    xbmc.log('wizard is located at: '+wizard_file)

    dialog_enable = None

    if os.path.isfile(wizard_file):
        file = open(wizard_file,'r')
        for l in file.readlines():
            if l == "wizard completed":
                dialog_enable = False
                xbmc.log('wizard file contains: '+l)
                file.close()
                break
        if dialog_enable == None:
            dialog_enable = True
    else:
        dialog_enable = True




    ##try:
    if dialog_enable == True:
        set_font_arial()
        lan_list = get_language_list(__cwd__)
        combined_list = get_string_list(__cwd__,lan_list,30000)
        if len(lan_list) > 0:
            dialog = xbmcgui.Dialog()
            answer = dialog.select('Please choose your language', combined_list[1])
            xbmc.log("answer"+str(answer))
            xbmc.log("language"+combined_list[0][answer])
        if answer != -1:
            language = combined_list[0][answer]
            xbmc.log("language"+language)
            if set_lan(language) == True:
                xbmc.log("shut down xbmc so the choosen language will take effect")
                xbmc.sleep(1000) # svn@19445 seems to be fine with that though, but other version I tried will hang if its too short
                #xbmc.executebuiltin('ReloadSkin()')
                #xbmc.executebuiltin('RestartApp()')
                #xbmc.executebuiltin('System.LogOff')
                #xbmc.executebuiltin('ReloadSkin()')
                file = open(wizard_file,'w')
                file.write('wizard completed')
                file.close()
                #xbmc.executebuiltin('Quit')
                os.system("sudo kill `pidof xbmc.bin`")
            else:
                file = open(wizard_file,'w')
                file.write('wizard completed')
                file.close()
        while answer == -1:
            lan_list = get_language_list(__cwd__)
            combined_list = get_string_list(__cwd__,lan_list,30000)
            if len(lan_list) > 0:
                dialog = xbmcgui.Dialog()
                answer = dialog.select('Please choose your language', combined_list[1])
                xbmc.log("answer"+str(answer))
                xbmc.log("language"+combined_list[0][answer])
            if answer != -1:
                language = combined_list[0][answer]
                xbmc.log("language"+language)
                if set_lan(language) == True:
                    xbmc.log("shut down xbmc so the choosen language will take effect")
                    xbmc.sleep(1000) # svn@19445 seems to be fine with that though, but other version I tried will hang if its too short
                    #xbmc.executebuiltin('ReloadSkin()')
                    #xbmc.executebuiltin('RestartApp()')
                    #xbmc.executebuiltin('System.LogOff')
                    #xbmc.executebuiltin('ReloadSkin()')
                    file = open(wizard_file,'w')
                    file.write('wizard completed')
                    file.close()
                    #xbmc.executebuiltin('Quit')
                    os.system("sudo kill `pidof xbmc.bin`")
                else:
                    file = open(wizard_file,'w')
                    file.write('wizard completed')
                    file.close()

    ##except:
    ##    xbmc.log('something wrong')
