#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla & PCD        *
*             skin by MMark            *
*             14/01/2023               *
*       Skin by MMark                  *
****************************************
#--------------------#
#Info http://t.me/tivustream
'''
from __future__ import print_function
from . import Utils
from . import html_conv
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarSeek
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarSeek
from Screens.InfoBarGenerics import InfoBarAudioSelection
from Screens.InfoBarGenerics import InfoBarSubtitleSupport
from Screens.InfoBarGenerics import InfoBarNotifications
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import SCOPE_PLUGINS
from Tools.Directories import pathExists
from Tools.Directories import resolveFilename
from enigma import RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT
from enigma import eListboxPythonMultiContent
from enigma import ePicLoad
from enigma import eServiceReference
from enigma import eTimer
from enigma import gFont
from enigma import iPlayableService
from enigma import loadPNG
from enigma import getDesktop
from twisted.web.client import downloadPage, getPage
import os
import re
import six
import sys
import json
import ssl
import requests
import urllib3

global skin_path

PY2 = False
PY3 = False
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# try:
    # from urllib.parse import urlparse
    # from urllib.request import Request
    # from urllib.request import urlopen
    # PY3 = True
# except:
    # from urlparse import urlparse
    # from urllib2 import Request
    # from urllib2 import urlopen

if PY3:
    bytes = bytes
    str = unicode = basestring = str
    range = range
    zip = zip

    def iteritems(d, **kw):
        return iter(d.items(**kw))

    from urllib.parse import quote
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import HTTPError, URLError

if PY2:
    _str = str
    str = unicode
    range = xrange
    from itertools import izip
    zip = izip
    unicode = unicode
    basestring = basestring

    def bytes(b, encoding="ascii"):
        return _str(b)

    def iteritems(d, **kw):
        return d.iteritems(**kw)

    from urlparse import urlparse
    from urllib import quote
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import HTTPError, URLError


currversion = '1.8'
cj = {}
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('Filmon'))
title_plug = 'Filmon Player'
desc_plugin = '..:: Live Filmon by Lululla %s ::.. ' % currversion
_firstStartfo = True

global skin_path
screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_newuhd.xml')
    if Utils.DreamOS():
        skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen_newuhd.xml')

elif screenwidth.width() == 1920:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_new.xml')
    if Utils.DreamOS():
        skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen_new.xml')
else:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen.xml')
    if Utils.DreamOS():
        skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen.xml')


if sys.version_info >= (2, 7, 9):
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

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


class SslOldHttpAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')

        self.poolmanager = urllib3.poolmanager.PoolManager(
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_context=ctx)


global tmp_image
tmp_image = '/tmp/filmon/poster.png'
if not pathExists('/tmp/filmon/'):
    os.system('mkdir /tmp/filmon/')
else:
    print('/tmp/filmon/ allready present')

os.system("cd / && cp -f " + PLUGIN_PATH + '/noposter.png' + ' /tmp/filmon/poster.png')
os.system("cd / && cp -f " + PLUGIN_PATH + '/noposter.jpg' + ' /tmp/filmon/poster.jpg')


class m2list(MenuList):

    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if screenwidth.width() == 2560:
            self.l.setItemHeight(70)
            textfont = int(42)
            self.l.setFont(0, gFont('Regular', textfont))        
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(60)
            textfont = int(30)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(35)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))

    
def show_(name, link, img, session, description):
    res = [(name,
            link,
            img,
            session,
            description)]
    page1 = os.path.join(PLUGIN_PATH, 'skin/images_new/50x50.png')
    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(60, 60), png=loadPNG(page1)))
        res.append(MultiContentEntryText(pos=(110, 0), size=(1200, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))    
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(50, 50), png=loadPNG(page1)))
        res.append(MultiContentEntryText(pos=(90, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 3), size=(40, 40), png=loadPNG(page1)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    if os.path.exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_conv.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", str(e))
        return True
    elif os.path.exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_conv.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", str(e))
        return True
    else:
        text_clear = html_conv.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True


class filmon(Screen):
    def __init__(self, session):
        self.session = session
        skin = skin_path
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        global _session
        _session = session
        self.menulist = []
        self.setTitle(title_plug)
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        # self['title'] = Label('')
        self['name'] = Label('Loading data... Please wait')
        self['text'] = Label('')
        self['poster'] = Pixmap()
        self.picload = ePicLoad()
        self.picfile = ''
        self.dnfile = 'False'
        self.currentList = 'menulist'
        self.loading_ok = False
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'DirectionActions',
                                     # 'ButtonSetupActions',
                                     'MovieSelectionActions'], {'up': self.up,
                                                                'down': self.down,
                                                                'left': self.left,
                                                                'right': self.right,
                                                                'ok': self.ok,
                                                                'cancel': self.exit,
                                                                'red': self.exit}, -1)
        self.onLayoutFinish.append(self.downxmlpage)

    def up(self):
        try:
            self[self.currentList].up()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            # print('get current: ', type(self.auswahl))
            self['name'].setText(self.auswahl)
            self.load_poster()
        except Exception as e:
            print(e)

    def down(self):
        try:
            self[self.currentList].down()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            # print('get current: ', type(self.auswahl))
            self['name'].setText(str(self.auswahl))
            self.load_poster()
        except Exception as e:
            print(e)

    def left(self):
        try:
            self[self.currentList].pageUp()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            # print('get current: ', type(self.auswahl))
            self['name'].setText(self.auswahl)
            self.load_poster()
        except Exception as e:
            print(e)

    def right(self):
        try:
            self[self.currentList].pageDown()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            # print('get current: ', type(self.auswahl))
            self['name'].setText(self.auswahl)
            self.load_poster()
        except Exception as e:
            print(e)

    def downxmlpage(self):
        url = 'http://www.filmon.com/group'
        if PY3:
            url = b'http://www.filmon.com/group'
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self):
        self['name'].setText(_('Try again later ...'))

    def _gotPageLoad(self, data):
        self.auswahl = ''
        self.index = 'group'
        self.cat_list = []
        global sessionx
        sessionx = self.get_session()
        url = data
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
        #  regexvideo = '<li class="group-item".*?a href="(.*?)".*?title="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(url)
        for url, img, name in match:
            img = img.replace('\\', '')
            url = "http://www.filmon.com" + url
            pic = ''
            url = Utils.checkStr(url)
            img = Utils.checkStr(img)
            name = Utils.checkStr(name)
            self.cat_list.append(show_(name, url, img, sessionx, pic))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].moveToIndex(0)
        self['name'].setText('Select')
        self.auswahl = self['menulist'].getCurrent()[0][0]
        # print('get current: ', self.auswahl)
        self['name'].setText(self.auswahl)
        self['text'].setText('')
        self.load_poster()

    def cat(self, url):
        self.auswahl = ''
        self.index = 'cat'
        self.cat_list = []
        self.id = ''
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        req.add_header('Referer', 'http://www.filmon.com/')
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
            img = Utils.checkStr(img)
            id = Utils.checkStr(id)
            self.id = id
            title = html_conv.html_unescape(title)
            description = html_conv.html_unescape(description)
            self.cat_list.append(show_(title, id, img, sessionx, description))
        self['menulist'].l.setList(self.cat_list)
        self['menulist'].moveToIndex(0)
        self.auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(self.auswahl))
        self.load_poster()

    def get_session(self):
        urlx = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
        req = Request(urlx)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        req.add_header('Referer', 'http://www.filmon.com/')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        page = urlopen(req, None, 15)
        content = page.read()
        if PY3:
            content = six.ensure_str(content)
        print('content: ', content)
        x = json.loads(content)
        session = ''
        session = x["session_key"]
        if session:
            print('session O ', str(session))
            return str(session)
        else:
            return 'none'

    def ok(self):
        try:
            if self.index == 'cat':
                id = self['menulist'].getCurrent()[0][1]
                print('iddddd : ', id)
                session = self['menulist'].getCurrent()[0][3]
                # id = Utils.checkStr(id)
                referer = 'http://www.filmon.com'
                urlx = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
                content = Utils.ReadUrl2(urlx, referer)
                regexvideo = 'session_key":"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                print("In Filmon2 fpage match =", match)
                url = 'http://www.filmon.com/api-v2/channel/' + str(id) + "?session_key=" + session
                self.get_rtmp(url)
            elif self.index == 'group':
                url = self['menulist'].getCurrent()[0][1]
                session = self['menulist'].getCurrent()[0][3]
                print('url: ', url)
                print('session: ', session)
                self.cat(url)
        except Exception as e:
            print(str(e))
            print("Error: can't find file")

    def get_rtmp(self, data):
        try:
            # import requests
            from urllib3.exceptions import InsecureRequestWarning
            from urllib3 import disable_warnings 
            disable_warnings(InsecureRequestWarning)

            referer = 'http://www.filmon.com'
            from . import client
            headers = {'User-Agent': client.agent(), 'Referer': referer}
            content = six.ensure_str(client.request(data, headers=headers))

            rtmp = re.findall('"quality".*?url"\:"(.*?)"', content)
            # print('rtmp: ', rtmp)
            if rtmp:
                fin_url = rtmp[0].replace('\\', '')
                print('fin_url: ', fin_url)
                self.play_that_shit(str(fin_url))
        except Exception as ex:
            print(ex)
            print("Error: can't read data")

    def play_that_shit(self, data):
        desc = self['menulist'].l.getCurrentSelection()[0][0]
        url = data
        name = desc
        self.session.open(Playstream2, name, url)

    def exit(self):
        if self.index == 'group':
            Utils.deletetmp()
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
        pixmaps = self['menulist'].getCurrent()[0][2]
        tmp_image = '/tmp/filmon/poster.png'

        if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
            if pixmaps.find('http') == -1:
                self.poster_resize(tmp_image)
                return
            else:
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(pixmaps)

                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, tmp_image, sniFactory, timeout=5).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, tmp_image).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
                except Exception as ex:
                    print(ex)
                    print("Error: can't find file or read data")
            return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass
            except:
                pass

    def downloadError(self, png):
        try:
            if os.path.exists(png):
                self.poster_resize(tmp_image)
        except Exception as ex:
            self.poster_resize(tmp_image)
            print(ex)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        if os.path.exists(png):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])
            if Utils.DreamOS():
                self.picload.startDecode(png, False)
            else:
                self.picload.startDecode(png, 0, 0, False)
            ptr = self.picload.getData()
            if ptr is not None:
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
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed, "hide": self.hide}, 0)
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

    def debug(obj, text=""):
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
        global streaml
        Screen.__init__(self, session)
        # global _session
        # _session = session
        self.session = session
        self.skinName = 'MoviePlayer'
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
        self.allowPiP = False
        self.service = None
        # self.stream = stream
        self.state = self.STATE_PLAYING
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'ColorActions',
                                     'DirectionActions',
                                     'ButtonSetupActions',
                                     'OkCancelActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'InfobarSeekActions'], {'stop': self.cancel,
                                                             'epg': self.showIMDB,
                                                             'info': self.showIMDB,
                                                             # 'info': self.cicleStreamType,
                                                             'tv': self.cicleStreamType,
                                                             'leavePlayer': self.cancel,
                                                             'back': self.leavePlayer,
                                                             # 'stop': self.leavePlayer,
                                                             'playpauseService': self.playpauseService,
                                                             'down': self.av,
                                                             'cancel': self.cancel}, -1)
        self.service = None
        self.url = url
        self.name = html_conv.html_unescape(name)
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        # self.onLayoutFinish.append(self.cicleStreamType)
        if '8088' in str(self.url):
            # self.onLayoutFinish.append(self.slinkPlay)
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            # self.onLayoutFinish.append(self.cicleStreamType)
            self.onFirstExecBegin.append(self.cicleStreamType)

        # self.onFirstExecBegin.append(self.openYtdl)    
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {
            0: '4:3 Letterbox',
            1: '4:3 PanScan',
            2: '16:9',
            3: '16:9 always',
            4: '16:10 Letterbox',
            5: '16:10 PanScan',
            6: '16:9 Letterbox'
        }[aspectnum]

    def setAspect(self, aspect):
        map = {
            0: '4_3_letterbox',
            1: '4_3_panscan',
            2: '16_9',
            3: '16_9_always',
            4: '16_10_letterbox',
            5: '16_10_panscan',
            6: '16_9_letterbox'
        }
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp += 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showIMDB(self):
        text_clear = self.name
        if returnIMDB(text_clear):
            print('show imdb/tmdb')

    def to_bytes(value, encoding='utf-8'):
        """
        Makes sure the value is encoded as a byte string.
        :param value: The Python string value to encode.
        :param encoding: The encoding to use.
        :return: The byte string that was encoded.
        """
        if isinstance(value, six.binary_type):
            return value
        return value.encode(encoding)
    def openPlay(self):
        try:
            self.session.nav.stopService()
            self.session.nav.playService(self.url)
        except Exception as e:
            print('error player ', e)

    def playpauseService(self):
        if self.state == self.STATE_PLAYING:
            self.pause()
            self.state = self.STATE_PAUSED
        elif self.state == self.STATE_PAUSED:
            self.unpause()
            self.state = self.STATE_PLAYING

    def pause(self):
        self.session.nav.pause(True)

    def unpause(self):
        self.session.nav.pause(False)
    def openYtdl(self):
        name = self.name
        url = 'streamlink%3a//' + self.url
        servicetype = '4097'
        ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference youtube:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def slinkPlay(self, url):
        ref = str(url)
        ref = ref.replace(':', '%3a').replace(' ', '%20')
        print('final reference 1:   ', ref)
        ref = "{0}:{1}".format(ref, self.name)
        sref = eServiceReference(ref)
        sref.setName(self.name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openTest(self, servicetype, url):
        url = url.replace(':', '%3a').replace(' ', '%20')
        ref = str(servicetype) + ':0:1:0:0:0:0:0:0:0:' + str(url)  # + ':' + self.name

        if streaml is True:
            ref = str(servicetype) + ':0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + str(url) + ':' + self.name

        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(self.name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streaml
        streaml = False
        from itertools import cycle, islice
        self.servicetype = '4097'
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(os.path.splitext(self.url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        currentindex = 0
        streamtypelist = ["4097"]
        '''
        if "youtube" in str(self.url):
            self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            return
        if isStreamlinkAvailable():
            streamtypelist.append("5002")
            streaml = True
        if os.path.exists("/usr/bin/gstplayer"):
            streamtypelist.append("5001")
        if os.path.exists("/usr/bin/exteplayer3"):
            streamtypelist.append("5002")
        '''
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

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback is not None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        # streaml = False
        self.leavePlayer()

    def leavePlayer(self):
        self.close()


class AutoStartTimerFon:

    def __init__(self, session):
        self.session = session
        global _firstStartfo
        print("*** running AutoStartTimerFon ***")
        if _firstStartfo:
            self.runUpdate()

    def runUpdate(self):
        print("*** running update ***")
        try:
            from . import Update
            Update.upd_done()
            _firstStartfo = False
        except Exception as e:
            print('error Fxy', str(e))


def autostart(reason, session=None, **kwargs):
    print("*** running autostart ***")
    global autoStartTimerFon
    global _firstStartfo
    if reason == 0:
        if session is not None:
            _firstStartfo = True
            autoStartTimerFon = AutoStartTimerFon(session)
    return


def main(session, **kwargs):
    try:
        session.open(filmon)
    except:
        import traceback
        traceback.print_exc()
        pass


def Plugins(**kwargs):
    icona = 'plugin.png'
    extDescriptor = PluginDescriptor(name='Filmon Player', description=desc_plugin, where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon=icona, fnc=main)
    result = [PluginDescriptor(name=title_plug, description=desc_plugin, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=title_plug, description=desc_plugin, where=PluginDescriptor.WHERE_PLUGINMENU, icon=icona, fnc=main)]
    result.append(extDescriptor)
    return result
