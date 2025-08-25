#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

"""
#########################################################
#                                                       #
#  Filmon Plugin                                        #
#  Version: 2.4                                         #
#  Created by Lululla                                   #
#  License: GPL-3.0-or-later                            #
#  https://www.gnu.org/licenses/gpl-3.0.html            #
#  Last Modified: 15:14 - 2025-08-24                    #
#                                                       #
#  Features:                                            #
#    - Access Filmon content                            #
#    - Browse categories, programs, and videos          #
#    - Play streaming video                             #
#    - JSON API integration                             #
#    - Debug logging                                    #
#    - User-friendly interface                          #
#                                                       #
#  Credits:                                             #
#    - Original development by Lululla                  #
#                                                       #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"

from json import loads as json_loads
from os import makedirs, remove
from os.path import exists, join
from re import compile, DOTALL, findall
from shutil import copy
from sys import version_info
from time import sleep
import random
import codecs

# Third-party imports
import six
from twisted.web.client import downloadPage, getPage

# Enigma2 core imports
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    ePicLoad,
    eServiceReference,
    eTimer,
    getDesktop,
    gFont,
    iPlayableService,
    loadPNG,
    iServiceInformation
)

# Enigma2 component imports
try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker

# Enigma2 screen imports
from Screens.InfoBarGenerics import (
    InfoBarAudioSelection,
    InfoBarMenu,
    InfoBarNotifications,
    InfoBarSeek,
    InfoBarSubtitleSupport
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import Setup

# Enigma2 tools imports
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from six.moves.urllib.request import Request, urlopen
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

# Plugin imports
from Plugins.Plugin import PluginDescriptor

# Local module imports
from . import _
from .lib import Utils
from .lib.html_conv import html_unescape

# global skin_path
CURR_VERSION = '2.4'
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('Filmon'))
TITLE_PLUG = 'Filmon Player'
DESC_PLUGIN = '..:: Live Filmon by Lululla %s ::.. ' % CURR_VERSION
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
TMP_IMAGE = '/tmp/filmon/poster.png'
aspect_manager = Utils.AspectManager()
disable_warnings(InsecureRequestWarning)
PY3 = version_info[0] == 3

config.plugins.filmon = ConfigSubsection()
config.plugins.filmon.token_refresh = ConfigYesNo(default=True)
config.plugins.filmon.token_refresh_interval = ConfigInteger(
    default=45, limits=(30, 300))

if PY3:
    from urllib.parse import urlparse
    unicode = str
else:
    from urlparse import urlparse
    str = unicode
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except ImportError:
        sslContext = None

try:
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except BaseException:
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
    # Python 3
    from urllib.error import HTTPError
except ImportError:
    # Python 2
    from urllib2 import HTTPError


# Check if the directory exists, if not, create it
if not exists('/tmp/filmon/'):
    makedirs('/tmp/filmon/')
else:
    print('/tmp/filmon/ already present')

try:
    copy(join(PLUGIN_PATH, 'noposter.png'), '/tmp/filmon/poster.png')
    copy(join(PLUGIN_PATH, 'noposter.jpg'), '/tmp/filmon/poster.jpg')
except Exception as e:
    print("Error copying files: {}".format(e))


def isStreamlinkAvailable():
    try:
        from os import popen
        popen('streamlink --version')
        return True
    except BaseException:
        return False


def isGstPlayerAvailable():
    return exists("/usr/bin/gstplayer")


# Set the skin path based on the screen resolution
screenwidth = getDesktop(0).size()
screen_width = screenwidth.width()  # Save the screen width in a variable
if screen_width == 2560:
    skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_newuhd.xml')
elif screen_width == 1920:
    skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_new.xml')
else:
    skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen.xml')

if exists('/var/lib/dpkg/status'):
    skin_path = skin_path.replace('skin_pli', 'skin_cvs')

skin_info = join(PLUGIN_PATH, 'skin/info/info.xml')


class m2list(MenuList):

    def __init__(self, items):
        MenuList.__init__(self, items, True, eListboxPythonMultiContent)
        screen_width = screenwidth.width()

        if screen_width == 2560:
            self.l.setItemHeight(70)
            self.l.setFont(0, gFont('Regular', 42))
        elif screen_width == 1920:
            self.l.setItemHeight(60)
            self.l.setFont(0, gFont('Regular', 30))
        else:
            self.l.setItemHeight(35)
            self.l.setFont(0, gFont('Regular', 24))


def show_(name, link, img, session, description):
    res = [(name, link, img, session, description)]
    page1 = join(PLUGIN_PATH, 'skin/images_new/50x50.png')
    screen_width = screenwidth.width()

    if screen_width == 2560:
        icon_pos, icon_size = (5, 5), (60, 60)
        text_pos, text_size = (110, 0), (1200, 50)
    elif screen_width == 1920:
        icon_pos, icon_size = (5, 5), (50, 50)
        text_pos, text_size = (90, 0), (1000, 50)
    else:
        icon_pos, icon_size = (3, 3), (40, 40)
        text_pos, text_size = (70, 0), (500, 50)

    res.append(
        MultiContentEntryPixmapAlphaTest(
            pos=icon_pos,
            size=icon_size,
            png=loadPNG(page1)))
    res.append(MultiContentEntryText(
        pos=text_pos,
        size=text_size,
        font=0,
        text=name,
        color=0xA6D1FE,
        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER
    ))

    return res


def returnIMDB(session, text_clear):
    """Show IMDB/TMDB information for the content"""
    text = html_unescape(text_clear)

    if Utils.is_TMDB and Utils.TMDB:
        try:
            session.open(Utils.TMDB.tmdbScreen, text, 0)
        except Exception as e:
            print("[DEBUG][XCF] TMDB error:", str(e))
        return True

    elif Utils.is_tmdb and Utils.tmdb:
        try:
            session.open(Utils.tmdb.tmdbScreen, text, 0)
        except Exception as e:
            print("[DEBUG][XCF] tmdb error:", str(e))
        return True

    elif Utils.is_imdb and Utils.imdb:
        try:
            Utils.imdb(session, text)
        except Exception as e:
            print("[DEBUG][XCF] IMDb error:", str(e))
        return True

    session.open(MessageBox, text, MessageBox.TYPE_INFO)
    return True


def get_session():
    urlx = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=livehttp'
    req = Request(urlx)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', 'http://www.filmon.com/')
    req.add_header('X-Requested-With', 'XMLHttpRequest')
    page = urlopen(req, None, 15)
    content = page.read()
    if PY3:
        content = six.ensure_str(content)
    x = json_loads(content)
    session = x["session_key"]
    if session:
        print('session: ', str(session))
        return str(session)
    else:
        return 'none'


class FilmonSettings(Setup):
    def __init__(self, session, parent=None):
        Setup.__init__(
            self,
            session,
            setup="FilmonSettings",
            plugin="Extensions/Filmon")
        self.parent = parent

    def keySave(self):
        Setup.keySave(self)


class filmon(Screen):
    def __init__(self, session):
        self.session = session

        with codecs.open(skin_path, "r", encoding="utf-8") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.menulist = []
        self.setTitle(TITLE_PLUG)
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['name'] = Label('Loading data... Please wait')
        self['text'] = Label()
        self['poster'] = Pixmap()
        self.picload = ePicLoad()
        self.picfile = ''
        self.dnfile = 'False'
        self.currentList = 'menulist'
        self.loading_ok = False
        self['actions'] = ActionMap(
            ['OkCancelActions',
             'ColorActions',
             'DirectionActions',
             # 'ButtonSetupActions',
             'ChannelSelectEPGActions',
             'MenuActions'],
            {
                'up': self.up,
                'down': self.down,
                'left': self.left,
                'right': self.right,
                'ok': self.ok,
                'cancel': self.exit,
                'info': self.infohelp,
                "menu": self.open_settings,
                'red': self.exit
            }, -1
        )

        self.onLayoutFinish.append(self.downxmlpage)

    def open_settings(self):
        self.session.open(FilmonSettings)

    def infohelp(self):
        self.session.open(FilmonInfo)

    def up(self):
        try:
            self[self.currentList].up()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            self['name'].setText(self.auswahl)
            self.load_poster()
        except Exception as e:
            print(e)

    def down(self):
        try:
            self[self.currentList].down()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            self['name'].setText(str(self.auswahl))
            self.load_poster()
        except Exception as e:
            print(e)

    def left(self):
        try:
            self[self.currentList].pageUp()
            self.auswahl = self['menulist'].getCurrent()[0][0]
            self['name'].setText(self.auswahl)
            self.load_poster()
        except Exception as e:
            print(e)

    def right(self):
        try:
            self[self.currentList].pageDown()
            self.auswahl = self['menulist'].getCurrent()[0][0]
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
        self.selection = ''
        self.index = 'group'
        self.category_list = []

        global sessionx
        sessionx = get_session()

        page_content = data
        if PY3:
            page_content = six.ensure_str(page_content)

        # print("page content =", page_content)

        try:
            start = page_content.find('<ul class="group-channels"', 0)
            end = page_content.find('<div id="footer">', start)
        except BaseException:
            start = page_content.find(b'<ul class="group-channels"', 0)
            end = page_content.find(b'<div id="footer">', start)

        content_block = page_content[start:end]

        regex = r'class="group-item".*?a href="(.*?)".*?logo" src="(.*?)".*?title="(.*?)"'
        matches = compile(regex, DOTALL).findall(content_block)

        for url, img, name in matches:
            img = img.replace('\\', '')
            url = "http://www.filmon.com" + url

            if PY3:
                url = six.ensure_str(url)
                img = six.ensure_str(img)
                name = six.ensure_str(name)
            else:
                if isinstance(url, unicode):
                    url = url.encode('utf-8')
                if isinstance(img, unicode):
                    img = img.encode('utf-8')
                if isinstance(name, unicode):
                    name = name.encode('utf-8')

            pic = ''
            self.category_list.append(show_(name, url, img, sessionx, pic))
            self.current_list_items = [(item[0], item[1])
                                       for item in self.category_list]

        self['menulist'].l.setList(self.category_list)
        self['menulist'].moveToIndex(0)
        self['name'].setText('Select')
        self.selection = self['menulist'].getCurrent()[0][0]
        self['name'].setText(self.selection)

        self.load_poster()

    def cat(self, url):
        self.selection = ''
        self.index = 'cat'
        self.category_list = []
        self.id = ''

        group_id = url.split('/')[-1]
        session = get_session()
        if not session:
            self['name'].setText(_('Session error, try again later ...'))
            return

        # Try API first
        api_url = 'https://eu-api.filmon.com/api/group/' + \
            group_id + '?session_key=' + session
        try:
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': 'http://www.filmon.com',
                'X-Requested-With': 'XMLHttpRequest'
            }
            req = Request(api_url, headers=headers)
            response = urlopen(req)
            content = response.read()
            if PY3:
                content = content.decode('utf-8')
            data = json_loads(content)
            channels = data.get('channels', [])

            if channels:
                for channel in channels:
                    channel_id = channel.get('id', '')
                    title = channel.get('title', '')
                    description = channel.get('description', '')
                    img = channel.get(
                        'big_logo', '') or channel.get(
                        'logo', '')
                    if img:
                        img = img.replace('\\', '')
                    self.category_list.append(
                        show_(
                            title,
                            channel_id,
                            img,
                            session,
                            description))
                    self.current_list_items = [
                        (item[0], item[1]) for item in self.category_list]

                self['menulist'].l.setList(self.category_list)
                self['menulist'].moveToIndex(0)
                self.selection = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(self.selection))
                self.load_poster()
                return

        except Exception as e:
            print("API error:", str(e))

        # If API fails, fallback to HTML parsing
        try:
            req = Request(url)
            req.add_header('User-Agent', USER_AGENT)
            req.add_header('Referer', 'http://www.filmon.com/')
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            page = urlopen(req)
            page_content = page.read()
            if PY3:
                page_content = six.ensure_str(page_content)

            regexvideo = r'data-channel-id="(.*?)".*?<img src="(.*?)".*?<a href=".*?">(.*?)</a>'
            matches = findall(regexvideo, page_content, DOTALL)

            for channel_id, img, title in matches:
                img = img.replace('\\', '')
                title = html_unescape(title)
                self.category_list.append(
                    show_(title, channel_id, img, session, ''))
                self.current_list_items = [
                    (item[0], item[1]) for item in self.category_list]

            self['menulist'].l.setList(self.category_list)
            self['menulist'].moveToIndex(0)
            self.selection = self['menulist'].getCurrent()[0][0]
            self['name'].setText(str(self.selection))
            self.load_poster()

        except Exception as e:
            print("HTML parsing error:", str(e))
            self['name'].setText(_('Error loading channels'))

    def onHlsSelected(self, selected_url, channelID, index, currentList):
        if selected_url:
            self.play_that_shit(
                selected_url,
                channelID,
                'hls',
                index,
                currentList)

    def ok(self):
        try:
            current_index = self['menulist'].getCurrent()
            if not current_index:
                return

            if self.index == 'cat':
                channel_id = current_index[0][1]
                print('Channel ID:', channel_id)
                session = get_session()
                if session:
                    url = f'https://eu-api.filmon.com/api/channel/{channel_id}?session_key={session}'
                    self.get_rtmp(url, channel_id)

            elif self.index == 'group':
                group_url = current_index[0][1]
                print('Group URL:', group_url)
                self.cat(group_url)

        except Exception as e:
            print("Error:", str(e))
            print("Error: can't find file")

    def get_rtmp(self, url, channel_id):
        try:
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': 'http://www.filmon.com',
                'X-Requested-With': 'XMLHttpRequest'
            }
            req = Request(url, headers=headers)
            response = urlopen(req, timeout=10)
            content = response.read()
            if PY3:
                content = content.decode('utf-8')
            data = json_loads(content)

            hls_streams = []
            streams = data.get('streams', [])

            for stream in streams:
                stream_url = stream.get('url', '')
                stream_name = stream.get('name', '')
                quality = stream.get('quality', '')

                if '.m3u8' in stream_url:
                    clean_url = stream_url.replace('\\', '')
                    if stream_name and quality:
                        display_name = "%s (%s)" % (stream_name, quality)
                    else:
                        display_name = "HLS Stream"
                    hls_streams.append(
                        {'url': clean_url, 'name': display_name})

            current_index = self['menulist'].getSelectedIndex()
            current_list = self.current_list_items

            if hls_streams:
                if len(hls_streams) > 1:
                    self.session.openWithCallback(
                        lambda selected: self.onHlsSelected(
                            selected,
                            channel_id,
                            current_index,
                            current_list),
                        HlsSelectionScreen,
                        hls_streams,
                        title=_("Select stream quality"))
                else:
                    self.play_that_shit(
                        str(hls_streams[0]['url']),
                        channel_id,
                        'hls',
                        current_index,
                        current_list
                    )

        except Exception as ex:
            print("Error reading API data:", ex)

    def fallback_hls(self, channel_id, streams):
        token = None

        # Extract token from the first URL that contains 'id='
        for stream in streams:
            url = stream.get('url', '')
            if 'id=' in url:
                token = url.split('id=')[1].split('&')[0].split('/')[0]
                break

        if token:
            base_url = "http://edge%s.filmon.com/live/%s.%s.stream/playlist.m3u8?id=%s"
            edge_server = random.randint(1300, 1400)

            hls_urls = [
                {'url': base_url % (edge_server, channel_id, 'high', token), 'name': 'High Quality'},
                {'url': base_url % (edge_server, channel_id, 'low', token), 'name': 'Low Quality'}
            ]

            fallback_url = hls_urls[1]['url']  # Low quality
            print('Fallback HLS URL:', fallback_url)
            self.play_that_shit(str(fallback_url), channel_id, 'hls')
        else:
            print("Token not found for fallback")
            self.session.open(
                MessageBox,
                _("Could not get stream token"),
                MessageBox.TYPE_INFO
            )

    def play_that_shit(
            self,
            url,
            channel_id,
            stream_type,
            index=None,
            current_list=None):

        if index is None:
            index = self['menulist'].getSelectedIndex()

        if current_list is None:
            current_list = self.current_list_items

        selected_item = current_list[index]
        name = selected_item[0][0]

        self.channelID = channel_id
        self.current_channel_url = url
        self.current_stream_url = url
        print("HLS URL player:", str(url))

        self.session.open(
            Playstream2,
            name,
            url,
            channel_id,
            stream_type,
            index,
            current_list
        )

    def exit(self):
        if self.index == 'group':
            Utils.deletetmp()
            self.close()
        elif self.index == 'cat':
            self.downxmlpage()

    def load_poster(self):
        global TMP_IMAGE

        current_item = self['menulist'].getCurrent()
        if not current_item:
            return

        # Set description if in category view
        if self.index == 'cat':
            description = current_item[0][4]
            print('Description:', description)
            self['text'].setText(description)
        else:
            self['text'].setText('')

        pixmap_url = current_item[0][2]
        TMP_IMAGE = '/tmp/filmon/poster.png'

        if pixmap_url and pixmap_url.lower() not in ("", "n/a", "null"):
            if 'http' not in pixmap_url:
                self.poster_resize(TMP_IMAGE)
                return
            else:
                try:
                    if PY3:
                        pixmap_url = six.ensure_binary(pixmap_url)

                    if pixmap_url.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmap_url)
                        domain = parsed_uri.hostname
                        sni_factory = SNIFactory(domain)
                        downloadPage(
                            pixmap_url,
                            TMP_IMAGE,
                            sni_factory,
                            timeout=5).addCallback(
                            self.downloadPic,
                            TMP_IMAGE).addErrback(
                            self.downloadError)

                    else:
                        downloadPage(
                            pixmap_url,
                            TMP_IMAGE).addCallback(
                            self.downloadPic,
                            TMP_IMAGE).addErrback(
                            self.downloadError)

                except Exception as ex:
                    print("Error: can't find file or read data", ex)

    def downloadPic(self, data, pictmp):
        if exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                self.poster_resize(TMP_IMAGE)

    def downloadError(self, png):
        try:
            if exists(png):
                self.poster_resize(TMP_IMAGE)
        except Exception as ex:
            self.poster_resize(TMP_IMAGE)
            print('exe downloadError', ex)

    def poster_resize(self, png_path):
        self['poster'].hide()

        if not exists(png_path):
            return

        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        scale = AVSwitch().getFramebufferScale()

        self.picload.setPara(
            [size.width(), size.height(), scale[0], scale[1], 0, 1, '#00000000'])

        if exists('/var/lib/dpkg/status'):
            self.picload.startDecode(png_path, False)
        else:
            self.picload.startDecode(png_path, 0, 0, False)

        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()


class HlsSelectionScreen(Screen):
    def __init__(self, session, hls_urls, title=_("Select stream quality")):
        Screen.__init__(self, session)
        self.skinName = ["HlsSelectionScreen", "Setup"]
        self.setTitle(title)
        self.hls_urls = hls_urls

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "red": self.cancel,
                "green": self.ok,
                "cancel": self.cancel,
                "ok": self.ok,
            },
            -2
        )
        self.list = []
        for stream in hls_urls:
            self.list.append((stream['name'], stream['url']))

        self["config"] = MenuList(self.list)
        self.selected_url = None

    def ok(self):
        selection = self["config"].getCurrent()
        if selection:
            self.selected_url = selection[1]
            self.close(self.selected_url)

    def cancel(self):
        self.close(None)


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    FLAG_CENTER_DVB_SUBS = 2048
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {
            "toggleShow": self.OkPressed,
            "hide": self.hide
        }, 0)

        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
            iPlayableService.evStart: self.serviceStarted
        })
        self.__state = self.STATE_SHOWN
        self.__locked = 0

        # Aggiungi l'help overlay come in Vavoo
        self.helpOverlay = Label("")
        self.helpOverlay.skinAttributes = [
            ("position", "0,0"),
            ("size", "1280,50"),
            ("font", "Regular;28"),
            ("halign", "center"),
            ("valign", "center"),
            ("foregroundColor", "#FFFFFF"),
            ("backgroundColor", "#666666"),
            ("transparent", "0"),
            ("zPosition", "100")
        ]

        self["helpOverlay"] = self.helpOverlay
        self["helpOverlay"].hide()

        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(
                self.doTimerHide)
        except BaseException:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(3000, True)  # Ridotto a 3 secondi come in Vavoo
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def show_help_overlay(self):
        help_text = (
            "OK = Info | CH+/CH- = PREV/NEXT CHANNEL | PLAY/PAUSE = Toggle | STOP = Stop | EXIT = Exit"
        )
        self["helpOverlay"].setText(help_text)
        self["helpOverlay"].show()

        self.help_timer = eTimer()
        self.help_timer.callback.append(self.hide_help_overlay)
        self.help_timer.start(5000, True)

    def hide_help_overlay(self):
        self["helpOverlay"].hide()

    def OkPressed(self):
        if self["helpOverlay"].visible:
            self.help_timer.stop()
            self.hide_help_overlay()
        else:
            self.show_help_overlay()
        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def serviceStarted(self):
        if self.execing and config.usage.show_infobar_on_zap.value:
            self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            self.hideTimer.start(3000, True)  # Ridotto a 3 secondi

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def toggleShow(self):
        if not self.skipToggleShow:
            if self.__state == self.STATE_HIDDEN:
                self.show()
                self.hideTimer.stop()
                self.show_help_overlay()

            else:
                self.hide()
                self.startHideTimer()

                if self["helpOverlay"].visible:
                    self.help_timer.stop()
                    self.hide_help_overlay()
        else:
            self.skipToggleShow = False

    def lockShow(self):
        try:
            self.__locked += 1
        except BaseException:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except BaseException:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()


class Playstream2(
        Screen,
        InfoBarMenu,
        InfoBarBase,
        InfoBarSeek,
        InfoBarNotifications,
        InfoBarAudioSelection,
        TvInfoBarShowHide,
        InfoBarSubtitleSupport):

    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(
            self,
            session,
            name,
            url,
            channelID,
            stream_type,
            index,
            currentList):

        Screen.__init__(self, session)

        self.session = session
        self.skinName = 'MoviePlayer'

        self.currentindex = index
        self.itemscount = len(currentList)
        self.list = currentList

        self.name = name
        self.url = url
        self.channelID = channelID
        self.current_channel_url = url
        self.current_stream_url = url

        self.stream_type = stream_type

        self.state = self.STATE_PLAYING
        self.servicetype = "4097"

        self.retry_count = 0
        self.max_retries = 3
        self.service_handler = None
        self.next_token_url = None
        self.is_buffering = False
        self.last_play_time = 0
        self.min_play_duration = 2000

        self.token_refresh_enabled = config.plugins.filmon.token_refresh.value
        self.refresh_interval = config.plugins.filmon.token_refresh_interval.value * 1000
        self.service_check_interval = 5000

        for base in [
            InfoBarMenu, InfoBarNotifications, InfoBarBase,
            TvInfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport
        ]:
            base.__init__(self)

        InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')
        self.__event_tracker = ServiceEventTracker(
            screen=self,
            eventmap={
                iPlayableService.evStart: self.serviceStarted,
                iPlayableService.evEOF: self.__evEOF,
                iPlayableService.evStopped: self.__evStopped,
                iPlayableService.evUser: self.__evUser,
            }
        )

        self.buffer_timer = eTimer()
        try:
            self.buffer_timer_conn = self.buffer_timer.timeout.connect(
                self.end_buffering)
        except BaseException:
            self.buffer_timer.callback.append(self.end_buffering)

        if self.token_refresh_enabled:
            self.refresh_timer = eTimer()
            try:
                self.refresh_timer_conn = self.refresh_timer.timeout.connect(
                    self.preventive_refresh)
            except BaseException:
                self.refresh_timer.callback.append(self.preventive_refresh)
            self.refresh_timer.start(self.refresh_interval, True)

        self.service_check_timer = eTimer()
        try:
            self.service_check_timer_conn = self.service_check_timer.timeout.connect(
                self.check_service_status)
        except BaseException:
            self.service_check_timer.callback.append(self.check_service_status)
        self.service_check_timer.start(10000, True)

        self.prefetch_timer = eTimer()
        try:
            self.prefetch_timer_conn = self.prefetch_timer.timeout.connect(
                self.prefetch_next_token)
        except BaseException:
            self.prefetch_timer.callback.append(self.prefetch_next_token)

        self.prefetch_timer.start(30000, True)

        self.connection_monitor_timer = eTimer()
        try:
            self.connection_monitor_timer_conn = self.connection_monitor_timer.timeout.connect(
                self.monitor_connection)
        except BaseException:
            self.connection_monitor_timer.callback.append(
                self.monitor_connection)
        self.connection_monitor_timer.start(
            30000, True)  # Controlla ogni 30 secondi

        self['actions'] = ActionMap(
            [
                "WizardActions",
                "MoviePlayerActions",
                "MovieSelectionActions",
                "MediaPlayerActions",
                "EPGSelectActions",
                "MediaPlayerSeekActions",
                "ColorActions",
                "ButtonSetupActions",
                "InfobarShowHideActions",
                "InfobarActions",
                "InfobarSeekActions"
            ],
            {
                'epg': self.showIMDB,
                'info': self.showIMDB,
                'stop': self.cancel,
                'leavePlayer': self.cancel,
                'prevBouquet': self.previousitem,
                'nextBouquet': self.nextitem,
                'channelDown': self.previousitem,
                'channelUp': self.nextitem,
                'down': self.previousitem,
                'up': self.nextitem,
                "cancel": self.cancel,
                "back": self.cancel,
                "playpauseService": self.playpauseService
            },
            -1
        )
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.log_service_events()
        self.openTest(self.servicetype, url)
        self.onClose.append(self.cancel)

    def log_service_events(self):
        """Log all service events for debugging"""
        print("Available iPlayableService events:")
        events = [
            ('evStart', iPlayableService.evStart),
            ('evEOF', iPlayableService.evEOF),
            ('evUser', iPlayableService.evUser),
        ]

        # Add only the events that actually exist
        for name, value in events:
            if hasattr(iPlayableService, name):
                print("{}: {}".format(name, value))
            else:
                print("{}: NOT AVAILABLE".format(name))

    def monitor_connection(self):
        """Monitor the connection status and recover if necessary"""
        try:
            service = self.session.nav.getCurrentService()
            if service is None:
                print("Connection monitor: Service is None, attempting to recover...")
                self.handle_stream_failure()
                return

            # Check if the service reference is still valid
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if not ref or not ref.valid():
                print(
                    "Connection monitor: Service reference is invalid, attempting to recover...")
                self.handle_stream_failure()
                return

        except Exception as e:
            print("Connection monitor error: " + str(e))

        # Reschedule the monitoring
        self.connection_monitor_timer.start(30000, True)

    def start_buffering(self):
        """Show buffering indicator"""
        if not self.is_buffering:
            self.is_buffering = True
            self.session.openWithCallback(
                self.buffering_callback,
                MessageBox,
                _("Buffering..."),
                MessageBox.TYPE_INFO,
                timeout=2)

    def end_buffering(self):
        """Hide buffering indicator"""
        self.is_buffering = False

    def buffering_callback(self, result=None):
        """Callback per il buffering"""
        self.is_buffering = False

    def preventive_refresh(self):
        """Preventive token refresh"""
        if not self.token_refresh_enabled:
            return

        print("Performing preventive token refresh...")
        new_url = self.regenerate_stream_url()
        if new_url:
            try:
                # Ensure the new URL is valid
                if not new_url.startswith('http'):
                    new_url = 'http://' + new_url

                encoded_url = new_url.replace(':', '%3a').replace(' ', '%20')
                ref = '{}:0:1:0:0:0:0:0:0:0:{}'.format(
                    self.servicetype, encoded_url)
                new_sref = eServiceReference(ref)
                new_sref.setName(self.name)

                # Stop the current service
                self.session.nav.stopService()
                sleep(0.1)

                # Start the new service
                self.session.nav.playService(new_sref)

                print("Stream updated successfully")

            except Exception as e:
                print("Error in preventive refresh: " + str(e))
                # Attempt recovery
                self.handle_stream_error()
        else:
            print("Cannot get valid URL for refresh")

        # Reschedule the timer
        if self.token_refresh_enabled:
            self.refresh_timer.start(self.refresh_interval, True)

    def prefetch_next_token(self):
        """Prefetch the next token in background"""
        if not self.token_refresh_enabled:
            return

        try:
            new_url = self.regenerate_stream_url()
            if new_url:
                self.next_token_url = new_url
                print("Next token prefetched successfully")

            # Reschedule prefetch
            self.prefetch_timer.start(
                self.refresh_interval - 10000,
                True)  # 10 seconds before refresh

        except Exception as e:
            print("Prefetch error: " + str(e))
            # Retry later
            self.prefetch_timer.start(15000, True)

    def openTest(self, servicetype, url):
        try:
            # Ensure the URL is complete and valid
            if not url.startswith('http'):
                url = 'http://' + url

            encoded_url = url.replace(':', '%3a').replace(' ', '%20')
            ref = '{}:0:1:0:0:0:0:0:0:0:{}'.format(servicetype, encoded_url)
            print('final reference:', ref)

            sref = eServiceReference(ref)
            sref.setName(self.name)

            # Stop the current service if it is playing
            current_service = self.session.nav.getCurrentService()
            if current_service is not None:
                self.session.nav.stopService()
                sleep(0.1)  # Short pause to allow closure

            # Start the new service
            self.session.nav.playService(sref)
            self.state = self.STATE_PLAYING

            # Restart the refresh timer
            if hasattr(self, 'refresh_timer') and self.token_refresh_enabled:
                self.refresh_timer.start(self.refresh_interval, True)

        except Exception as e:
            print("Error in openTest:", str(e))
            self.handle_stream_error()

    def get_current_time_ms(self):
        """Return current time in milliseconds"""
        import time
        return int(round(time.time() * 1000))

    def restart_stream(self, new_url):
        """Restart the stream"""
        try:
            # Prepare the new service reference
            encoded_url = new_url.replace(':', '%3a').replace(' ', '%20')
            ref = '4097:0:1:0:0:0:0:0:0:0:' + str(encoded_url)
            new_sref = eServiceReference(ref)
            new_sref.setName(self.name)

            # Direct transition
            self.session.nav.stopService()
            sleep(0.02)
            self.session.nav.playService(new_sref)

        except Exception as e:
            print("Error restarting stream: " + str(e))
            self.handle_stream_error()

    def up(self):
        pass

    def down(self):
        self.up()

    def nextitem(self):
        self.currentindex += 1
        if self.currentindex >= len(self.list):
            self.currentindex = 0
        self.update_channel()

    def previousitem(self):
        self.currentindex -= 1
        if self.currentindex < 0:
            self.currentindex = len(self.list) - 1
        self.update_channel()

    def update_channel(self):
        if not self.list:
            return
        if self.currentindex >= len(self.list) or self.currentindex < 0:
            return

        # Get the channel info from the list
        channel_info = self.list[self.currentindex]
        self.name = channel_info[0][0]
        channel_id = channel_info[0][1]

        # Update the current channel ID
        self.channelID = channel_id

        # Get the session key
        session = channel_info[0][3]

        if session and channel_id:
            url = "https://eu-api.filmon.com/api/channel/" + \
                str(channel_id) + "?session_key=" + session
            self.get_rtmp_update(url, channel_id)

    def get_rtmp_update(self, data, channelID):
        try:
            referer = "http://www.filmon.com"
            headers = {
                "User-Agent": USER_AGENT,
                "Referer": referer,
                "X-Requested-With": "XMLHttpRequest"
            }
            req = Request(data, headers=headers)
            response = urlopen(req, timeout=10)
            content = response.read()
            if PY3:
                content = content.decode("utf-8")
            json_data = json_loads(content)

            hls_urls = []
            streams = json_data.get("streams", [])
            """
            # for stream in streams:
                # url = stream.get("url", "")
                # if ".m3u8" in url:
                    # hls_url = url.replace("\\", "")
                    # hls_urls.append({"url": hls_url})
            """
            if hls_urls:
                self.url = hls_urls[0]["url"]
                self.current_stream_url = self.url
                self.openTest(self.servicetype, self.url)
            else:
                self.fallback_hls_update(channelID, streams)
        except Exception as ex:
            print("Error updating stream:", ex)

    def fallback_hls_update(self, channelID, streams):
        # Similar to the fallback_hls method but for updating
        token = None
        for stream in streams:
            url = stream.get('url', '')
            if 'id=' in url:
                token = url.split('id=')[1].split('&')[0].split('/')[0]
                break

        if token:
            base_url = "http://edge{}.filmon.com/live/{}.{}.stream/playlist.m3u8?id={}"
            edge_server = random.randint(1300, 1400)
            self.url = base_url.format(edge_server, channelID, 'high', token)
            self.openTest(self.servicetype, self.url)

    def serviceStarted(self):
        """Service started successfully"""
        self.retry_count = 0
        import time
        print("Service started successfully at", time.strftime("%H:%M:%S"))

        # Check that playback has actually started
        if not self.check_stream_playback():
            print("Playback verification failed, attempting recovery...")
            self.handle_stream_error()
            return

        service = self.session.nav.getCurrentService()
        if service:
            info = service.info()
            print(
                "Service info:",
                info.getInfoString(
                    iServiceInformation.sServiceref))

    def __evEOF(self):
        """End of stream reached"""
        print("EOF detected, attempting to reconnect...")
        self.handle_stream_error()

    def __evUser(self, event):
        """Eventi utente/errori"""
        try:
            # GST_ERROR è tipicamente evUser + 12
            if event == iPlayableService.evUser + 12:
                print("GStreamer error detected, attempting to recover...")
                # Non chiamare handle_stream_error immediatamente, prima
                # verifica lo stato
                service = self.session.nav.getCurrentService()
                if service is None:
                    self.handle_stream_failure()
                else:
                    # Potrebbe essere un errore temporaneo, aspetta un po'
                    # prima di agire
                    self.recovery_timer = eTimer()
                    try:
                        self.recovery_timer_conn = self.recovery_timer.timeout.connect(
                            self.check_stream_recovery)
                    except BaseException:
                        self.recovery_timer.callback.append(
                            self.check_stream_recovery)
                    self.recovery_timer.start(2000, True)
        except Exception as e:
            print(f"Error in user event handler: {str(e)}")

    def check_stream_recovery(self):
        """Verifica se lo stream si è ripreso dopo un errore"""
        service = self.session.nav.getCurrentService()
        if service is None:
            self.handle_stream_failure()
        else:
            # Controlla se il servizio è ancora in errore
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if not ref or not ref.valid():
                self.handle_stream_failure()

    def check_service_status(self):
        """Periodically check service status"""
        try:
            service = self.session.nav.getCurrentService()
            if service is None:
                print("Service is None, attempting to reconnect...")
                self.handle_stream_error()
                return

            # Check if the service reference is still valid
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if ref and ref.valid():
                # Service is active, continue monitoring after 5 seconds
                self.service_check_timer.start(5000, True)
            else:
                print("Service reference is invalid, attempting to reconnect...")
                self.handle_stream_error()
        except Exception as e:
            print("Error checking service status: " + str(e))
            self.handle_stream_error()

    def check_stream_playback(self):
        """Check if the stream is playing correctly"""
        try:
            service = self.session.nav.getCurrentService()
            if service is None:
                print("No current service - playback might have failed")
                return False

            # Check the status of the service
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if ref is None or not ref.valid():
                print("Service reference is invalid")
                return False

            return True

        except Exception as e:
            print("Error checking playback: " + str(e))
            return False

    def __evStopped(self):
        """Service stopped"""
        print("Service stopped")

    def handle_stream_error(self):
        """Handles stream errors"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            print("Attempting reconnect {}/{}".format(self.retry_count, self.max_retries))

            # Stop all timers temporarily
            if hasattr(self, 'refresh_timer') and self.token_refresh_enabled:
                self.refresh_timer.stop()
            if hasattr(self, 'service_check_timer'):
                self.service_check_timer.stop()

            # Regenerate the URL and restart
            new_url = self.regenerate_stream_url()
            if new_url:
                print("New URL generated: {}...".format(new_url[:100]))
                self.restart_stream(new_url)
            else:
                self.session.open(
                    MessageBox,
                    _("Cannot regenerate stream URL"),
                    MessageBox.TYPE_ERROR)
                self.close()
        else:
            self.session.open(
                MessageBox,
                _("Maximum reconnection attempts reached"),
                MessageBox.TYPE_ERROR)
            self.close()

    def doEofInternal(self, playing):
        if playing and self.retry_count < self.max_retries:
            self.retry_count += 1
            print("Tentativo di riconnessione", self.retry_count)
            self.retry_timer = eTimer()
            try:
                self.retry_timer_conn = self.retry_timer.timeout.connect(
                    self.retry_playback)

            except AttributeError:
                self.retry_timer.callback.append(self.retry_playback)
            self.retry_timer.start(2000, True)
        else:
            self.close()

    def handle_stream_failure(self):
        """Handle stream failures when preventive refresh fails"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            print(
                "Stream failure detected, attempt {}/{}".format(self.retry_count, self.max_retries))

            # Try to regenerate the session completely
            global sessionx
            sessionx = get_session()

            # Retry refresh after a short delay
            self.timer = eTimer()
            try:
                self.timer_conn = self.timer.timeout.connect(self.retry_stream)
            except BaseException:
                self.timer.callback.append(self.retry_stream)
            self.timer.start(3000, True)
        else:
            print("Max retries reached, giving up")
            self.session.open(
                MessageBox,
                _("Cannot restore stream connection"),
                MessageBox.TYPE_ERROR)
            self.close()

    def retry_stream(self):
        """Attempt to restore the stream after a failure"""
        new_url = self.regenerate_stream_url()
        if new_url:
            self.session.nav.stopService()
            self.openTest(self.servicetype, new_url)
        else:
            self.handle_stream_failure()

    def retry_playback(self):
        new_url = self.regenerate_stream_url()
        if new_url:
            self.session.nav.stopService()
            self.openTest(self.servicetype, new_url)

        else:
            self.close()

    def do_retry(self):
        new_url = self.regenerate_stream_url()
        if new_url:
            self.session.nav.stopService()
            self.openTest(self.servicetype, new_url)
        else:
            self.close()

    def regenerate_stream_url(self):
        try:
            session = get_session()
            if not session:
                return None

            api_url = "https://eu-api.filmon.com/api/channel/" + \
                str(self.channelID) + "?session_key=" + session
            headers = {
                "User-Agent": USER_AGENT,
                "Referer": "http://www.filmon.com",
                "X-Requested-With": "XMLHttpRequest"
            }

            req = Request(api_url, headers=headers)
            response = urlopen(req, timeout=10)
            content = response.read()
            if PY3:
                content = content.decode("utf-8")

            data = json_loads(content)
            streams = data.get("streams", [])

            # Look for a valid HLS stream first
            for stream in streams:
                stream_url = stream.get("url", "")
                if ".m3u8" in stream_url and "id=" in stream_url:
                    clean_url = stream_url.replace("\\", "")
                    # Ensure the URL is complete
                    if not clean_url.startswith("http"):
                        clean_url = "http://" + clean_url
                    return clean_url

            # Fallback to manual URL construction
            token = None
            for stream in streams:
                url = stream.get("url", "")
                if "id=" in url:
                    token = url.split("id=")[1].split("&")[0].split("/")[0]
                    break

            if token:
                base_url = "http://edge{}.filmon.com/live/{}.{}.stream/playlist.m3u8?id={}"
                edge_server = random.randint(1300, 1400)
                url = base_url.format(
                    edge_server, self.channelID, "high", token)
                return url

        except HTTPError as e:
            if e.code == 403:
                print("HTTP 403 Forbidden error - session might be expired")
                global sessionx
                sessionx = get_session()
                return self.regenerate_stream_url()
            else:
                print("HTTP Error {}: {}".format(e.code, e.reason))
        except Exception as e:
            print("Error regenerating stream: " + str(e))

        return None

    def playpauseService(self):
        """Toggle play/pause"""
        service = self.session.nav.getCurrentService()
        if not service:
            print("[WARNING] No current service")
            return

        pauseable = service.pause()
        if pauseable is None:
            print("[WARNING] Service is not pauseable")
            # Instead of failing, just stop and restart the service
            if self.state == self.STATE_PLAYING:
                current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
                if current_ref:
                    self.session.nav.stopService()
                    self.state = self.STATE_PAUSED
                    print("[DEBUG]Info: Playback stopped (pause not supported)")

            elif self.state == self.STATE_PAUSED:
                current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
                if current_ref:
                    self.session.nav.playService(current_ref)
                    self.show()
                    self.state = self.STATE_PLAYING
                    print("[DEBUG]Info: Playback resumed (pause not supported)")
            return

        try:
            if self.state == self.STATE_PLAYING:
                if hasattr(pauseable, "pause"):
                    pauseable.pause()
                    self.state = self.STATE_PAUSED
                    print("[DEBUG]Info: Playback paused")
            elif self.state == self.STATE_PAUSED:
                if hasattr(pauseable, "play"):
                    pauseable.play()
                    self.state = self.STATE_PLAYING
                    print("[DEBUG]Info: Playback resumed")
        except Exception as e:
            print("[ERROR]: Play/pause error: " + str(e))
            self.show_error(_("Play/pause not supported for this stream"))

    def show_error(self, message):
        """Show error message and close player"""
        self.session.openWithCallback(
            self.leavePlayer,
            MessageBox,
            message,
            MessageBox.TYPE_ERROR
        )

    def showIMDB(self):
        """Show IMDB/TMDB information"""
        returnIMDB(self.session, self.name)

    def pause(self):
        self.session.nav.pause(True)

    def unpause(self):
        self.session.nav.pause(False)

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self, *args):
        if hasattr(self, 'refresh_timer') and self.token_refresh_enabled:
            self.refresh_timer.stop()

        if hasattr(self, 'timer'):
            self.timer.stop()

        if hasattr(self, 'service_check_timer'):
            self.service_check_timer.stop()

        if exists('/tmp/hls.avi'):
            remove('/tmp/hls.avi')

        self.session.nav.stopService()
        if self.srefInit:
            self.session.nav.playService(self.srefInit)
        aspect_manager.restore_aspect()
        self.close()

    def leavePlayer(self, *args):
        self.session.nav.stopService()
        if self.srefInit:
            self.session.nav.playService(self.srefInit)
        self.close()


class FilmonInfo(Screen):
    def __init__(self, session):
        self.session = session
        skin = skin_info
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        Screen.__init__(self, session)

        name = _('WELCOME TO FILMON PLUGIN BY LULULLA')
        self['poster'] = Pixmap()
        self['title'] = Label(name)
        self['text'] = Label("")
        self.help_text = ""
        self.scroll_pos = 0

        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions'], {
            'ok': self.close,
            'cancel': self.close,
            'up': self.scrollUp,
            'down': self.scrollDown
        }, -2)

        self.onLayoutFinish.append(self.finishLayout)

    def scrollUp(self):
        if self.scroll_pos > 0:
            self.scroll_pos -= 1
            self.updateText()

    def scrollDown(self):
        self.scroll_pos += 1
        self.updateText()

    def updateText(self):
        lines = self.help_text.split('\n')
        if self.scroll_pos >= len(lines):
            self.scroll_pos = 0

        display_text = '\n'.join(lines[self.scroll_pos:self.scroll_pos + 20])
        self['text'].setText(display_text)

    def finishLayout(self):
        self.showHelp()

    def showHelp(self):
        self.help_text = "\n".join([
            "Filmon Plugin",
            "Version: " + CURR_VERSION,
            "Created by: Lululla",
            "License: GPL-3.0-or-later",
            "",
            "Features:",
            " - Access Filmon content",
            " - Browse categories, programs, and videos",
            " - Play streaming video",
            " - JSON API integration",
            " - Debug logging",
            " - User-friendly interface",
            "",
            "Credits:",
            " - Original development by Lululla",
            "",
            "Usage:",
            " Press OK to play the selected video",
            " Press Back to return",
            "",
            "Enjoy Filmon streaming!"
        ])

        self.updateText()


def main(session, **kwargs):
    try:
        session.open(filmon)
    except BaseException:
        import traceback
        traceback.print_exc()
        pass


def setup(session, **kwargs):
    session.open(FilmonSettings)


def Plugins(**kwargs):
    icona = 'plugin.png'

    extDescriptor = PluginDescriptor(
        name='Filmon Player',
        description=DESC_PLUGIN,
        where=PluginDescriptor.WHERE_EXTENSIONSMENU,
        icon=icona,
        fnc=main)
    setupDescriptor = PluginDescriptor(
        name='Filmon Setup',
        description="Configure Filmon settings",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon=icona,
        fnc=setup)
    result = [
        PluginDescriptor(
            name=TITLE_PLUG,
            description=DESC_PLUGIN,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=icona,
            fnc=main)]

    result.append(extDescriptor)
    result.append(setupDescriptor)
    return result
