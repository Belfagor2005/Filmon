# -*- coding: utf-8 -*-
#!/usr/bin/python
#--------------------#
#  coded by Lululla  #
#   skin by MMark    #
#     09/01/2021     #
#--------------------#
#Info http://t.me/tivustream
# from __future__ import print_function
#from albatros plugins
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.GUIComponent import GUIComponent
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MovingPixmap
from Components.MultiContent import MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import eConsoleAppContainer, eServiceReference, iPlayableService, eListboxPythonMultiContent
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from enigma import ePicLoad, loadPNG, getDesktop
from enigma import gFont, gPixmapPtr,  eTimer, eListbox
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import *
from Screens.InfoBar import MoviePlayer, InfoBar
from twisted.web.client import downloadPage, getPage, error
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, pathExists
from Tools.LoadPixmap import LoadPixmap
from Components.AVSwitch import AVSwitch
from Tools.BoundFunction import boundFunction
from socket import gaierror, error
from time import strptime, mktime
from Components.Console import Console as iConsole
import os
import re
import sys
import glob
import time
import socket
import sha
import shutil
import hashlib
from time import *
from sys import version_info

PY3 = sys.version_info[0] == 3
global isDreamOS, skin_path

isDreamOS = False

if PY3 :
    import http.cookiejar
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
    from urllib.parse import quote, unquote_plus, unquote, urlencode
    from http.client import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

else:
    import cookielib
    from urllib2 import Request, URLError, urlopen
    import urllib, urllib2
    from urllib import quote, unquote_plus, unquote, urlencode
    from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

try:
    from enigma import eMediaDatabase
    isDreamOS = True
except:
    isDreamOS = False

cj = {}

currversion = '1.4'
PLUGIN_PATH  = os.path.dirname(sys.modules[__name__].__file__)
skin_path= PLUGIN_PATH +'/skin'
title_plug = '..:: Filmon V. %s ::..' % currversion
desc_plugin = ('..:: Filmon by Lululla %s ::.. ' % currversion)

HD = getDesktop(0).size()
if HD.width() > 1280:
    Height = 60
    if isDreamOS:
        skin_path = skin_path + '/skin_cvs/defaultListScreen_new.xml'
    else:
        skin_path = skin_path + '/skin_pli/defaultListScreen_new.xml'
else:
    Height = 40
    if isDreamOS:
        skin_path = skin_path + '/skin_cvs/defaultListScreen.xml'
    else:
        skin_path = skin_path + '/skin_pli/defaultListScreen.xml'


from enigma import addFont
try:
    addFont('%s/1.ttf' % PLUGIN_PATH, 'RegularIPTV', 100, 1)
except Exception as ex:
    print('addfont', ex)

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer/plugin.pyo'):
    from Plugins.Extensions.MediaPlayer import *
    MediaPlayerInstalled = True
else:
    MediaPlayerInstalled = False


global tmp_image
tmp_image='/tmp/filmon/poster.png'
if not pathExists('/tmp/filmon/'):
    os.system('mkdir /tmp/filmon/')
else:
    print('/tmp/filmon/ allready present')

os.system("cd / && cp -f " + PLUGIN_PATH+'/noposter.png' + ' /tmp/filmon/poster.png')
os.system("cd / && cp -f " + PLUGIN_PATH+'/noposter.jpg' + ' /tmp/filmon/poster.jpg')

class m2list(MenuList):

    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setFont(0, gFont('Regular', 14))
        self.l.setFont(1, gFont('Regular', 16))
        self.l.setFont(2, gFont('Regular', 18))
        self.l.setFont(3, gFont('Regular', 20))
        self.l.setFont(4, gFont('Regular', 22))
        self.l.setFont(5, gFont('Regular', 24))
        self.l.setFont(6, gFont('Regular', 26))
        self.l.setFont(7, gFont('Regular', 28))
        self.l.setFont(8, gFont('Regular', 32))


def show_(name, link, img, session, description):
    res = [(name,
      link,
      img,
      session,
      description)]
    res.append(MultiContentEntryText(pos=(0, 0), size=(800, 40), font=8, text=name, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER))
    return res


def cat_(letter, link):
    res = [(letter, link)]
    res.append(MultiContentEntryText(pos=(0, 0), size=(800, 40), font=8, text=letter, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER))
    return res

class filmon(Screen):

    def __init__(self, session):
        self.session = session
        skin = skin_path
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions',
         'ColorActions',
         'DirectionActions',
         'MovieSelectionActions'], {'up': self.up,
         'down': self.down,
         'left': self.left,
         'right': self.right,
         'ok': self.ok,
         'cancel': self.exit,
         'red': self.exit}, -1)
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['title'] = Label(title_plug)
        self['name'] = Label('')
        self['text'] = Label('')
        self['poster'] = Pixmap()
        self.picload = ePicLoad()
        self.picfile = ''
        self.dnfile = 'False'
        self.currentList = 'menulist'
        self.menulist = []
        self.loading_ok = False
        self.check = 'abc'
        self.count = 0
        self.loading = 0
        self.onLayoutFinish.append(self.downxmlpage)

    def up(self):
        self[self.currentList].up()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def downxmlpage(self):
        url = 'http://www.filmon.com/group'
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self, error):
        print(str(error))
        self['name'].setText(_('Try again later ...'))

    def _gotPageLoad(self, data):
        self.index = 'group'
        self.cat_list = []
        global sessionx
        sessionx = self.get_session()
        url= data
        n1 = url.find('<ul class="group-channels"', 0)
        n2 = url.find('<div id="footer">', n1)
        url = url[n1:n2]
        regexvideo = '<li class="group-item".*?a href="(.*?)".*?logo" src="(.*?)".*?title="(.*?)"'
        match = re.compile(regexvideo,re.DOTALL).findall(url)
        for url, img, name in match:
            img = img.replace('\\', '')
            url = "http://www.filmon.com" + url
            pic = ''
            self.cat_list.append(show_(name, url, img, sessionx,pic))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].l.setItemHeight(40)
        self['menulist'].moveToIndex(0)
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self['text'].setText('')
        self.load_poster()

    def cat(self,url):
        self.index = 'cat'
        self.cat_list = []
        url=url
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        req.add_header('Referer', 'https://www.filmon.com/')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        page = urlopen(req)
        r = page.read()
        n1 = r.find('channels"', 0)
        n2 = r.find('channels_count"', n1)
        r2 = r[n1:n2]
        channels = re.findall('"id":(.*?),"logo":".*?","big_logo":"(.*?)","title":"(.*?)",.*?description":"(.*?)"', r2)
        for id, img,title, description in channels:
            img = img.replace('\\', '')
            url = url
            description = description
            self.cat_list.append(show_(title, id, img, sessionx, description))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].l.setItemHeight(40)
        self['menulist'].moveToIndex(0)
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def get_session(self):
        url = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        page = urlopen(req)
        r = page.read()
        session = re.findall('"session_key":"(.*?)"', r)
        if session:
            return str(session[0])
        else:
            return 'none'

    def ok(self):
        if self.index == 'cat':
            id = self['menulist'].getCurrent()[0][1]
            session = self['menulist'].getCurrent()[0][3]
            url = 'https://www.filmon.com/ajax/getChannelInfo?channel_id=%s' % str(id)
            print('url: ', url)
            print('cj: ', cj)
            getPage(url, timeout=8, method='GET', cookies=cj, headers={'Host':'www.filmon.com','X-Requested-With':'XMLHttpRequest','Referer':'https://www.filmon.com','User-Agent': 'Android'}).addCallback(self.get_rtmp)

        elif self.index == 'group':
            url = self['menulist'].getCurrent()[0][1]
            session = self['menulist'].getCurrent()[0][3]
            print('url: ', url)
            print('session: ', session)
            self.cat(url)


    def get_rtmp(self, data):
        print(data)
        rtmp = re.findall('"quality":"high","url":"(.*?)"', data)
        if rtmp:
            first = rtmp[0].replace('\\', '')
            fin_url = first
            print('fin_url: ', fin_url)
            self.play_that_shit(fin_url)

    def play_that_shit(self, data):
        desc = self['menulist'].l.getCurrentSelection()[0][0]
        url = data
        name = desc
        self.session.open(Playstream2, name, url)


    def exit(self):
        if self.index == 'group':
            self.close()
        elif self.index == 'cat':
            self.downxmlpage()

    def load_poster(self):
        global tmp_image
        jp_link = self['menulist'].getCurrent()[0][2]
        tmp_image = jpg_store = '/tmp/filmon/poster.png'
        if fileExists(tmp_image):
            tmp_image = '/tmp/filmon/poster.png'
        else:
            m = hashlib.md5()
            m.update(jp_link)
            tmp_image = m.hexdigest()
        if self.index == 'cat':
            descriptionX = self['menulist'].getCurrent()[0][4]
            print('description: ', descriptionX)
            self['text'].setText(descriptionX)
        else:
            self['text'].setText('')
        test = self['menulist'].getCurrent()[0][1]
        try:
            downloadPage(jp_link, tmp_image).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
        except Exception as ex:
            print(ex)
            print("Error: can't find file or read data")

    def downloadError(self, raw):
        try:
            os.system("cd / && cp -f " + PLUGIN_PATH+'/noposter.png' + ' /tmp/filmon/poster.png')
        except Exception as ex:
            print(ex)
            print('exe downloadError')

    def downloadPic(self, data, jpg_store):
        if fileExists(jpg_store):
            self.poster_resize(jpg_store)
        else:
            print('logo not found')

    def poster_resize(self, poster_path):
        if isDreamOS:
            self['poster'].instance.setPixmap(gPixmapPtr())
        else:
            self['poster'].instance.setPixmap(None)
        self['poster'].hide()
        sc = AVSwitch().getFramebufferScale()
        self.picload = ePicLoad()
        size = self['poster'].instance.size()
        self.picload.setPara((size.width(),
         size.height(),
         sc[0],
         sc[1],
         False,
         1,
         '#FF000000'))

        if not isDreamOS:
            if self.picload.startDecode(poster_path, 0, 0, False) == 0:
                ptr = self.picload.getData()
                if ptr != None:
                    self['poster'].instance.setPixmap(ptr)
                    self['poster'].show()
                else:
                    print('no cover.. error')
            return
        else:
            if self.picload.startDecode(poster_path,False) == 0:
                ptr = self.picload.getData()
                if ptr != None:
                    self['poster'].instance.setPixmap(ptr)
                    self['poster'].show()
                else:
                    print('no cover.. error')
            return

class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarShowHide):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.skinName = 'MoviePlayer'
        title = 'Play'
        self['list'] = MenuList([])
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self)
        InfoBarShowHide.__init__(self)
        self['actions'] = ActionMap(['WizardActions',
         'MoviePlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarActions'], {'leavePlayer': self.cancel,
         'back': self.cancel}, -1)
        self.allowPiP = False
        InfoBarSeek.__init__(self, actionmap='MediaPlayerSeekActions')
        url = url.replace(':', '%3a')
        self.url = url
        self.name = name
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        url = self.url
        pass
        ref = '4097:0:1:0:0:0:0:0:0:0:' + url
        sref = eServiceReference(ref)
        sref.setName(self.name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefOld)
        self.close()

    def keyLeft(self):
        self['text'].left()

    def keyRight(self):
        self['text'].right()

    def keyNumberGlobal(self, number):
        self['text'].number(number)

def main(session, **kwargs):
    session.open(filmon)


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    return [PluginDescriptor(name=title_plug, description=desc_plugin, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main), PluginDescriptor(name=title_plug, description=desc_plugin, where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=main, icon='plugin.png')]
