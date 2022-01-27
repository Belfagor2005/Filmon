# -*- coding: utf-8 -*-
#!/usr/bin/python
#--------------------#
#  coded by Lululla  #
#   skin by MMark    #
#     25/01/2022     #
#--------------------#
#Info http://t.me/tivustream
from __future__ import print_function
# from . import _
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Console import Console as iConsole
from Components.GUIComponent import GUIComponent
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.StaticText import StaticText
from Components.config import *
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarSeek, InfoBarAudioSelection, InfoBarMoviePlayerSummarySupport, \
    InfoBarSubtitleSupport, InfoBarSummarySupport, InfoBarServiceErrorPopupSupport, InfoBarNotifications
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, pathExists
from Tools.LoadPixmap import LoadPixmap
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from enigma import eConsoleAppContainer, eListboxPythonMultiContent
from enigma import ePicLoad, loadPNG
from enigma import gFont, gPixmapPtr, eTimer, eListbox
from enigma import eServiceCenter
from enigma import eServiceReference
from enigma import eSize 
from enigma import iServiceInformation
from enigma import quitMainloop
from enigma import iPlayableService 
from os.path import splitext
from os.path import exists as file_exists
from socket import gaierror, error
from sys import version_info
from time import *
from time import strptime, mktime
from twisted.web.client import downloadPage, getPage, error
import glob
import hashlib
import os
import re
import shutil
import six
import sys
import time
try:
    from Plugins.Extensions.Filmon.Utils import *
except:
    from . import Utils
global skin_path

PY3 = False
PY3 = sys.version_info.major >= 3
print('Py3: ',PY3)

try:
    import http.cookiejar as cookielib
    from urllib.parse import urlencode
    from urllib.parse import quote
    from urllib.parse import urlparse
    from urllib.request import Request
    from urllib.request import urlopen
    PY3 = True; unicode = str; unichr = chr; long = int; xrange = range
except:
    import cookielib
    from urllib import urlencode
    from urllib import quote
    from urlparse import urlparse
    from urllib2 import Request
    from urllib2 import urlopen

try:
    from html.entities import name2codepoint as n2cp
    from http.client import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

except:
    from htmlentitydefs import name2codepoint as n2cp
    from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

currversion = '1.6'
cj = {}
PLUGIN_PATH  = os.path.dirname(sys.modules[__name__].__file__)
skin_path= PLUGIN_PATH +'/skin'
title_plug = '..:: Filmon Player ::..'
desc_plugin = '..:: Live Filmon by Lululla %s ::.. ' % currversion

if isFHD():
    Height = 60
    if DreamOS():
        skin_path = skin_path + '/skin_cvs/defaultListScreen_new.xml'
    else:
        skin_path = skin_path + '/skin_pli/defaultListScreen_new.xml'
else:
    Height = 40
    if DreamOS():
        skin_path = skin_path + '/skin_cvs/defaultListScreen.xml'
    else:
        skin_path = skin_path + '/skin_pli/defaultListScreen.xml'
try:
    from OpenSSL import SSL
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except:
    sslverify = False

if sslverify:
    class SNIFactory(ssl.ClientContextFactory):
        def __init__(self, hostname=None):
            self.hostname = hostname
            
        def getContext(self):
            ctx = self._contextFactory(self.method)
            if self.hostname:
                ClientTLSOptions(self.hostname, ctx)
            return ctx

try:
    from enigma import addFont
    addFont('%s/1.ttf' % PLUGIN_PATH, 'RegularIPTV', 100, 1)
except Exception as e:
    print('addfont', str(e))

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
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        self.l.setItemHeight(50)
        textfont = int(24)
        self.l.setFont(0, gFont('Regular', textfont))        
        if isFHD():
            self.l.setItemHeight(50)
            textfont = int(34)
            self.l.setFont(0, gFont('Regular', textfont))


def show_(name, link, img, session, description):
    res = [(name,
      link,
      img,
      session,
      description)]
    page1 = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin/images_new/page_select.png".format('Filmon'))
    res.append(MultiContentEntryPixmapAlphaTest(pos = (10, 12), size = (34, 25), png = loadPNG(page1)))
    res.append(MultiContentEntryText(pos=(60, 0), size=(1000, 50), font=0, text=name, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER))
    return res

def cat_(letter, link):
    res = [(letter, link)]
    # page2 = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin/images_new/page_select.png".format('Filmon'))    
    # res.append(MultiContentEntryPixmapAlphaTest(pos = (10, 10), size = (34, 25), png = loadPNG(page2)))    
    res.append(MultiContentEntryText(pos=(60, 0), size=(1000, 50), font=0, text=letter, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER))
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
        self.menulist = []
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
        self.loading_ok = False
        # self.check = 'abc'
        # self.count = 0
        # self.loading = 0
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
        if PY3:
            url = b'http://www.filmon.com/group'
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
        if PY3:
            url = six.ensure_str(url)
        print("content 3 =", url)
        try:
            n1 = url.find('<ul class="group-channels"', 0)
            n2 = url.find('<div id="footer">', n1)
        except:
            n1 = url.find(b'<ul class="group-channels"', 0)
            n2 = url.find(b'<div id="footer">', n1)
        url = url[n1:n2]
        regexvideo = 'class="group-item".*?a href="(.*?)".*?logo" src="(.*?)".*?title="(.*?)"'
        match = re.compile(regexvideo,re.DOTALL).findall(url)
        for url, img, name in match:
            img = img.replace('\\', '')
            url = "http://www.filmon.com" + url
            pic = ''
            url = checkStr(url)
            img = checkStr(img)
            name = checkStr(name)
            self.cat_list.append(show_(name, url, img, sessionx, pic))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].l.setItemHeight(50)
        self['menulist'].moveToIndex(0)
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self['text'].setText('')
        self.load_poster()

    def cat(self,url):
        self.index = 'cat'
        self.cat_list = []
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        req.add_header('Referer', 'https://www.filmon.com/')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        page = urlopen(req)
        r = page.read()
        if PY3:
            r = six.ensure_str(r)
        print("content 3 =", r)
        try:
            n1 = r.find('channels"', 0)
            n2 = r.find('channels_count"', n1)
        except:
            n1 = r.find('channels"', 0)
            n2 = r.find('channels_count"', n1)
        r2 = r[n1:n2]
        channels = re.findall('"id":(.*?),"logo":".*?","big_logo":"(.*?)","title":"(.*?)",.*?description":"(.*?)"', r2)
        for id, img, title, description in channels:
            img = img.replace('\\', '')
            id = checkStr(id)
            img = checkStr(img)
            title = checkStr(title)
            description = checkStr(description)
            self.cat_list.append(show_(title, id, img, sessionx, description))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].l.setItemHeight(50)
        self['menulist'].moveToIndex(0)
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(auswahl)
        self.load_poster()

    def get_session(self):
        if sys.version_info.major == 3:
             import urllib.request as urllib2
        elif sys.version_info.major == 2:
             import urllib2
        url = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        r = urllib2.urlopen(req,None,15)
        link = r.read()
        r.close()
        tlink = link
        if str(type(tlink)).find('bytes') != -1:
            try:
                tlink = tlink.decode("utf-8")
            except Exception as e:
                   print("Error: %s." % str(e))
        session = re.findall('"session_key":"(.*?)"', tlink)
        if session:
            return str(session[0])
        else:
            return 'none'

    def ok(self):
        try:
            if self.index == 'cat':
                name = self['menulist'].getCurrent()[0][0]
                id = self['menulist'].getCurrent()[0][1]
                print('iddddd : ', id)
                session = self['menulist'].getCurrent()[0][3]
                id = checkStr(id)
                urlx = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
                content = ReadUrl2(urlx)
                regexvideo = 'session_key":"(.*?)"'
                match = re.compile(regexvideo,re.DOTALL).findall(content)
                print("In Filmon2 fpage match =", match)
                url = 'https://www.filmon.com/api-v2/channel/' + id + "?session_key=" + session
                self.get_rtmp(url)

            elif self.index == 'group':
                url = self['menulist'].getCurrent()[0][1]
                session = self['menulist'].getCurrent()[0][3]
                print('url: ', url)
                print('session: ', session)
                self.cat(url)

        except Exception as e:
            print(str(e))
            print("Error: can't find file or read data")


    def get_rtmp(self, data):
        try:
            print('i m here-------')
            content = ReadUrl2(data)
            rtmp = re.findall('"quality".*?url"\:"(.*?)"', content)
            if rtmp:
                fin_url = rtmp[0].replace('\\', '')
                print('fin_url: ', fin_url)
                self.play_that_shit(str(fin_url))
        except Exception as e:
            print(str(e))
            print("Error: can't find file or read data")


    def play_that_shit(self, data):
        desc = self['menulist'].l.getCurrentSelection()[0][0]
        url = data
        name = desc
        self.session.open(Playstream2, name, url)

    def exit(self):
        if self.index == 'group':
            deletetmp()
            self.close()
        elif self.index == 'cat':
            self.downxmlpage()

    def load_poster(self):
        global tmp_image
        if self.index == 'cat':
            descriptionX = self['menulist'].getCurrent()[0][4]
            print('description: ', descriptionX)
            self['text'].setText(descriptionX)
        else:
            self['text'].setText('')
        jp_link = self['menulist'].getCurrent()[0][2]
        tmp_image = jpg_store = '/tmp/filmon/poster.png'

        if tmp_image != None or idx != -1:
            pixmaps = six.ensure_binary(jp_link)
            print("debug: pixmaps:",pixmaps)
            print("debug: pixmaps:",type(pixmaps))
            path = urlparse(pixmaps).path
            ext = splitext(path)[1]
            tmp_image = b'/tmp/posterx' + ext
            if file_exists(tmp_image):
                tmp_image = b'/tmp/posterx' + ext

            else:
                m = hashlib.md5()
                m.update(pixmaps)
                tmp_image = m.hexdigest()
            try:
                if pixmaps.startswith(b"https") and sslverify:
                    parsed_uri = urlparse(pixmaps)
                    domain = parsed_uri.hostname
                    sniFactory = SNIFactory(domain)
                    if PY3 == 3:
                        pixmaps = pixmaps.encode()
                    print('uurrll: ', pixmaps)
                    downloadPage(pixmaps, tmp_image, sniFactory, timeout=5).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
                else:
                    downloadPage(pixmaps, tmp_image).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
            except Exception as e:
                print(str(e))
                print("Error: can't find file or read data")
            return

    def downloadError(self, raw):
        try:
            if file_exists(tmp_image):
                self.poster_resize(tmp_image)
            else:
                os.system("cd / && cp -f " + PLUGIN_PATH+'/noposter.png' + ' /tmp/filmon/poster.png')
                self.poster_resize(tmp_image)
        except Exception as e:
            print(str(e))
            print('exe downloadError')


    def downloadPic(self, data, tmp_image):
        if file_exists(tmp_image):
            self.poster_resize(tmp_image)
        else:
            print('logo not found')

    def poster_resize(self, poster_path):
            self["poster"].show()
            pixmaps = poster_path
            if DreamOS():
                self['poster'].instance.setPixmap(gPixmapPtr())
            else:
                self['poster'].instance.setPixmap(None)
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
            ptr = self.picload.getData()
            if DreamOS():
                if self.picload.startDecode(pixmaps, False) == 0:
                    ptr = self.picload.getData()
            else:
                if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                    ptr = self.picload.getData()
            if ptr != None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
            else:
                print('no cover.. error')
            return

class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed,
         "hide": self.hide}, 0)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def toggleShow(self):
        if self.skipToggleShow:
            self.skipToggleShow = False
            return
        if self.__state == self.STATE_HIDDEN:
            self.show()
            self.hideTimer.stop()
        else:
            self.hide()
            self.startHideTimer()

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()
    def lockShow(self):
        try:
            self.__locked += 1
        except:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()

    def debug(obj, text = ""):
        print(text + " %s\n" % obj)

class Playstream2(
    InfoBarBase,
    InfoBarMenu,
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarSubtitleSupport,
    InfoBarNotifications,
    TvInfoBarShowHide,
    Screen
):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(self, session, name, url):
        global SREF, streaml
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        self.skinName = 'MoviePlayer'
        title = name
        streaml = False

        for x in InfoBarBase, \
                InfoBarMenu, \
                InfoBarSeek, \
                InfoBarAudioSelection, \
                InfoBarSubtitleSupport, \
                InfoBarNotifications, \
                TvInfoBarShowHide:
            x.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self['actions'] = ActionMap(['MoviePlayerActions',
         'MovieSelectionActions',
         'MediaPlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'SetupActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarActions',
         'InfobarSeekActions'], {'stop': self.cancel,
         'epg': self.showIMDB,
         'info': self.showinfo,
         # 'info': self.cicleStreamType,
         'tv': self.cicleStreamType,
         # 'stop': self.leavePlayer,
         'cancel': self.cancel,
         'back': self.cancel}, -1)
        self.allowPiP = False
        self.service = None
        service = None
        self.url = url
        self.pcip = 'None'
        self.name = decodeHtml(name)
        self.state = self.STATE_PLAYING
        SREF = self.session.nav.getCurrentlyPlayingServiceReference()
        # self.onLayoutFinish.append(self.cicleStreamType)
        if '8088' in str(self.url):
            # self.onLayoutFinish.append(self.slinkPlay)
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            # self.onLayoutFinish.append(self.cicleStreamType)
            self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: _('4:3 Letterbox'),
         1: _('4:3 PanScan'),
         2: _('16:9'),
         3: _('16:9 always'),
         4: _('16:10 Letterbox'),
         5: _('16:10 PanScan'),
         6: _('16:9 Letterbox')}[aspectnum]

    def setAspect(self, aspect):
        map = {0: '4_3_letterbox',
         1: '4_3_panscan',
         2: '16_9',
         3: '16_9_always',
         4: '16_10_letterbox',
         5: '16_10_panscan',
         6: '16_9_letterbox'}
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp = temp + 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showinfo(self):
        debug = True
        sTitle = ''
        sServiceref = ''
        try:
            servicename, serviceurl = getserviceinfo(sref)
            if servicename != None:
                sTitle = servicename
            else:
                sTitle = ''
            if serviceurl != None:
                sServiceref = serviceurl
            else:
                sServiceref = ''
            currPlay = self.session.nav.getCurrentService()
            sTagCodec = currPlay.info().getInfoString(iServiceInformation.sTagCodec)
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            message = 'stitle:' + str(sTitle) + '\n' + 'sServiceref:' + str(sServiceref) + '\n' + 'sTagCodec:' + str(sTagCodec) + '\n' + 'sTagVideoCodec:' + str(sTagVideoCodec) + '\n' + 'sTagAudioCodec : ' + str(sTagAudioCodec)
            self.mbox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def showIMDB(self):
        TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
        IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
        if os.path.exists(TMDB):
            from Plugins.Extensions.TMBD.plugin import TMBD
            text_clear = self.name
            text = charRemove(text_clear)
            self.session.open(TMBD, text, False)
        elif os.path.exists(IMDb):
            from Plugins.Extensions.IMDb.plugin import IMDB
            text_clear = self.name
            text = charRemove(text_clear)
            self.session.open(IMDB, text)
        else:
            text_clear = self.name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def slinkPlay(self, url):
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openTest(self, servicetype, url):
        name = self.name
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference:   ', ref)
        if streaml == True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streml
        streaml = False
        from itertools import cycle, islice
        self.servicetype = '4097'
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        currentindex = 0
        streamtypelist = ["4097"]
        # if "youtube" in str(self.url):
            # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # return
        if isStreamlinkAvailable():
            streamtypelist.append("5002") #ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            streaml = True
        if os.path.exists("/usr/bin/gstplayer"):
            streamtypelist.append("5001")
        if os.path.exists("/usr/bin/exteplayer3"):
            streamtypelist.append("5002")
        if os.path.exists("/usr/bin/apt-get"):
            streamtypelist.append("8193")
        for index, item in enumerate(streamtypelist, start=0):
            if str(item) == str(self.servicetype):
                currentindex = index
                break
        nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        self.servicetype = str(next(nextStreamType))
        print('servicetype2: ', self.servicetype)
        self.openTest(self.servicetype, url)

    def up(self):
        pass

    def down(self):
        self.up()

    def doEofInternal(self, playing):
        self.close()

    def __evEOF(self):
        self.end = True

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.isfile('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(SREF)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        streaml = False
        self.close()

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback != None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def leavePlayer(self):
        self.close()

def checks():
    from Plugins.Extensions.Filmon.Utils import checkInternet
    checkInternet()
    chekin= False
    if checkInternet():
        chekin = True
    return chekin

def main(session, **kwargs):
    if checks:
        try:
            from Plugins.Extensions.Filmon.Update import upd_done
            upd_done()
        except:
            pass
# def main(session, **kwargs):
    session.open(filmon)

def Plugins(**kwargs):
    icona = 'plugin.png'
    extDescriptor = PluginDescriptor(name=title_plug, description=desc_plugin, where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon=icona, fnc=main)
    result = [PluginDescriptor(name=title_plug, description=desc_plugin, where=[PluginDescriptor.WHERE_PLUGINMENU], icon=icona, fnc=main)]
    result.append(extDescriptor)
    return result
