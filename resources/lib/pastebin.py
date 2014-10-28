#!/usr/bin/env python
# Written by Stephane Graber <stgraber@stgraber.org>
#            Daniel Bartlett <dan@f-box.org>
# Last modification : Mon Jan 28 22:33:23 CET 2008

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




import urllib, os, sys, re, getopt, xml.dom.minidom, gettext
try:
    import json # For python 2.6 and newer
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None
from gettext import gettext as _
import configobj


# Custom urlopener to handle 401's
class pasteURLopener(urllib.FancyURLopener):
    def http_error_401(self, url, fp, errcode, errmsg, headers, data=None):
        return None

def preloadPastebins():
    # Check several places for config files:
    #  - global config in /etc/pastebin.d
    #  - for source checkout, config in the checkout
    #  - user's overrides in ~/.pastebin.d
    # Files found later override files found earlier.
    pastebind = {}
    for confdir in ['/usr/share/pastebin.d','/etc/pastebin.d','/usr/local/etc/pastebin.d',
                    os.path.expanduser('~/.pastebin.d'),
                    os.path.join(os.path.dirname(__file__), 'pastebin.d')]:
        try:
            confdirlist = os.listdir(confdir)
        except OSError:
            continue

        for fileitem in confdirlist:
            if fileitem.startswith('.'):
                continue

            filename = os.path.join(confdir, fileitem)
            try:
                bininstance = configobj.ConfigObj(filename)
            except configobj.ConfigObjError, e:
                print >> sys.stderr, '%s: %s' % (filename, e)
                continue

            try:
                section = bininstance['pastebin']
            except KeyError:
                print >> sys.stderr, _('%s: no section [pastebin]') % filename
                continue

            try:
                basename = section['basename']
            except KeyError:
                print >> sys.stderr, _("%s: no 'basename' in [pastebin]") % filename
                continue

            pastebind[basename] = bininstance
    return pastebind

# pastey.net obfuscates parent ids for replies.  Rather than taking the
# post ID given as the parent ID, we must handle this by going to that
# post page and looking up what the invisible parent ID field will be
# set to for children.
def doParentFixup(website, paramname, parentid):
    if parentid == "":
        return ""
    url_opener = pasteURLopener()
    page = url_opener.open(website + '/' + parentid, None)
    matches = re.split('<input.*?name="' + paramname + '".*?value="(.*?)"', page.read())
    if len(matches) <= 1 or re.match(parentid, matches[1]) == None:
        # The obfuscated version didn't begin with the partial version,
        # or unable to find the obfuscated version for some reason!
        # Create a paste with no parent (should we throw, instead?)
        return ""
    return matches[1]

#Return the parameters depending of the pastebin used
def getParameters(website, pastebind, content, user, jabberid, version, format, parentpid, permatag, title, username, password):
    "Return the parameters array for the selected pastebin"
    params = {}
    for pastebin in pastebind:
        if re.search(pastebind[pastebin]['pastebin']['regexp'], website):
            if "sizelimit" in pastebind[pastebin]['pastebin']:
                params['sizelimit'] = pastebind[pastebin]['pastebin']['sizelimit']

            for param in pastebind[pastebin]['format'].keys():
                paramname = pastebind[pastebin]['format'][param]
                if param == 'user':
                    params[paramname] = user
                elif param == 'content':
                    params[paramname] = content
                elif param == 'title':
                    params[paramname] = title
                elif param == 'version':
                    params[paramname] = version
                elif param == 'format':
                    params[paramname] = format
                elif param == 'parentpid':
                    params[paramname] = doParentFixup(website, paramname, parentpid)
                elif param == 'permatag':
                    params[paramname] = permatag
                elif param == 'username':
                    params[paramname] = username
                elif param == 'password':
                    params[paramname] = password
                elif param == 'jabberid':
                    params[paramname] = jabberid
                else:
                    params[paramname] = pastebind[pastebin]['defaults'][param]
    if params:
        return params
    else:
        sys.exit(_("Unknown website, please post a bugreport to request this pastebin to be added (%s)") % website)

#XML Handling methods
def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.encode('utf-8')

def getNodes(nodes, title):
    return nodes.getElementsByTagName(title)

def getFirstNode(nodes, title):
    return getNodes(nodes, title)[0]

def getFirstNodeText(nodes, title):
    return getText(getFirstNode(nodes, title).childNodes)

def paste_data(content):
    gettext.textdomain("pastebinit")

    version = "1.3" #Version number to show in the usage
    configfile = os.path.expanduser("~/.pastebinit.xml")
    defaultPB = "http://paste.ubuntu.com" #Default pastebin

    # Set defaults
    website = defaultPB
    user = os.environ.get('USER')
    jabberid = ""
    title = ""
    permatag = ""
    format = "text"
    username = ""
    password = ""
    filename = ""
    parentpid = ""

    #Example configuration file string
    configexample = """\
<pastebinit>
<pastebin>http://paste.debian.net</pastebin>
<author>A pastebinit user</author>
<jabberid>nobody@nowhere.org</jabberid>
<format>text</format>
</pastebinit>
"""

    #Open configuration file if it exists
    try:
        f = open(configfile)
        configtext = f.read()
        f.close()
        gotconfigxml = True
    except KeyboardInterrupt:
        sys.exit(_("KeyboardInterrupt caught."))
    except:
        gotconfigxml = False

    #Parse configuration file
    if gotconfigxml:
        try:
            configxml = xml.dom.minidom.parseString(configtext)
            for variable,key in (('pastebin','website'),('author','user'),('format','format'),('jabberid','jabberid')):
                try:
                    value = getFirstNodeText(configxml, variable)
                    vars()[key]=value
                except:
                    pass
        except KeyboardInterrupt:
            sys.exit(_("KeyboardInterrupt caught."))
        except:
            print _("Error parsing configuration file!")
            print _("Please ensure that your configuration file looks similar to the following:")
            print configexample
            sys.exit(1)


    pastebind = preloadPastebins() #get the config from /etc/pastebin.d/

    params = getParameters(website, pastebind, content, user, jabberid, version, format, parentpid, permatag, title, username, password) #Get the parameters array

    if not website.endswith("/"):
        website += "/"

    if "sizelimit" in params:
        if len(content) > int(params['sizelimit']):
            sys.exit(_("The content you are trying to send exceeds the pastebin's size limit."))
        else:
            del params['sizelimit']

    reLink = None
    tmp_page = ""
    if "page" in params:
        website += params['page']
        tmp_page = params['page']
        del params["page"]
    if "regexp" in params:
        reLink = params['regexp']
        del params["regexp"]
    if "target_url" in params:
        target_url = params["target_url"]
        del params["target_url"]
    else:
        target_url = None
    if 'post_format' in params:
        post_format = params['post_format']
        del params['post_format']
    else:
        post_format = 'standard'

    url_opener = pasteURLopener()

    if post_format == 'json':
        if json:
            params = json.dumps(params)
            url_opener.addheader('Content-type: text/json')
        else:
            sys.exit(_("Could not find any json library."))
    else:
        params = urllib.urlencode(params) #Convert to a format usable with the HTML POST

    page = url_opener.open(website, params) #Send the informations and be redirected to the final page

    try:
        if reLink: #Check if we have to apply a regexp
            if target_url:
                website = target_url
            else:
                website = website.replace(tmp_page, "")

            if reLink == '(.*)':
                return page.read().strip()
            else:
                return website + re.split(reLink, page.read())[1] #Print the result of the Regexp
        else:
            return page.url #Get the final page and show the ur
    except:
        return None


