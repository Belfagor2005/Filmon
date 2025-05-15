#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             skin by MMark            *
*             28/08/2023               *
*       Skin by MMark                  *
****************************************
#--------------------#
#Info http://t.me/tivustream
'''
from __future__ import print_function
# Standard library imports
import codecs
from json import loads as json_loads
from os import makedirs, remove
from os.path import exists, join
from re import compile, DOTALL, findall
from shutil import copy
from datetime import datetime
from sys import version_info

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
)

# Enigma2 component imports
try:
	from Components.AVSwitch import AVSwitch
except ImportError:
	from Components.AVSwitch import eAVControl as AVSwitch
from Components.ActionMap import ActionMap
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
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Enigma2 tools imports
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

# Plugin imports
from Plugins.Plugin import PluginDescriptor

# Local module imports
from . import _
from .lib import Utils
from .lib import html_conv
from .lib.Console import Console as xConsole

global skin_path

PY3 = version_info[0] == 3

if PY3:
	from urllib.parse import urlparse
	from urllib.request import urlopen, Request
	from urllib.error import URLError, HTTPError
	unicode = str
	xrange = range
	unichr = chr
	long = int
else:
	from urllib2 import urlopen, Request
	from urllib2 import URLError, HTTPError
	from urlparse import urlparse
	str = unicode
	unicode = unicode
	xrange = xrange
	try:
		import ssl
		sslContext = ssl._create_unverified_context()
	except:
		sslContext = None

currversion = '2.3'
cj = {}
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('Filmon'))
title_plug = 'Filmon Player'
desc_plugin = '..:: Live Filmon by Lululla %s ::.. ' % currversion
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS9GaWxtb24vbWFpbi9pbnN0YWxsZXIuc2g='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvRmlsbW9u'
aspect_manager = Utils.AspectManager()

try:
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


# Define the path for the tmp image
tmp_image = '/tmp/filmon/poster.png'

# Check if the directory exists, if not, create it
if not exists('/tmp/filmon/'):
	makedirs('/tmp/filmon/')
else:
	print('/tmp/filmon/ already present')

# Copy the image files to the desired location
try:
	copy(join(PLUGIN_PATH, 'noposter.png'), '/tmp/filmon/poster.png')
	copy(join(PLUGIN_PATH, 'noposter.jpg'), '/tmp/filmon/poster.jpg')
except Exception as e:
	print("Error copying files: {}".format(e))


class m2list(MenuList):

	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)
		screen_width = screenwidth.width()  # Save the screen width in a variable
		if screen_width == 2560:
			self.l.setItemHeight(70)
			textfont = int(42)
			self.l.setFont(0, gFont('Regular', textfont))
		elif screen_width == 1920:
			self.l.setItemHeight(60)
			textfont = int(30)
			self.l.setFont(0, gFont('Regular', textfont))
		else:
			self.l.setItemHeight(35)
			textfont = int(24)
			self.l.setFont(0, gFont('Regular', textfont))


def show_(name, link, img, session, description):
	res = [(name, link, img, session, description)]
	page1 = join(PLUGIN_PATH, 'skin/images_new/50x50.png')

	screen_width = screenwidth.width()  # Save the screen width in a variable

	if screen_width == 2560:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(60, 60), png=loadPNG(page1)))
		res.append(MultiContentEntryText(pos=(110, 0), size=(1200, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
	elif screen_width == 1920:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(50, 50), png=loadPNG(page1)))
		res.append(MultiContentEntryText(pos=(90, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
	else:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 3), size=(40, 40), png=loadPNG(page1)))
		res.append(MultiContentEntryText(pos=(70, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))

	return res


# Set the skin path based on the screen resolution
screenwidth = getDesktop(0).size()
screen_width = screenwidth.width()  # Save the screen width in a variable

# Unified logic to determine the skin_path based on resolution and DreamOS
if screen_width == 2560:
	skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_newuhd.xml')
elif screen_width == 1920:
	skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_new.xml')
else:
	skin_path = join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen.xml')

# Add support for DreamOS
if Utils.DreamOS():
	skin_path = skin_path.replace('skin_pli', 'skin_cvs')


def returnIMDB(text_clear):
	text = html_conv.html_unescape(text_clear)
	if Utils.is_TMDB:
		try:
			from Plugins.Extensions.TMBD.plugin import TMBD
			_session.open(TMBD.tmdbScreen, text, 0)
		except Exception as e:
			print("[XCF] Tmdb: ", str(e))
		return True

	elif Utils.is_tmdb:
		try:
			from Plugins.Extensions.tmdb.plugin import tmdb
			_session.open(tmdb.tmdbScreen, text, 0)
		except Exception as e:
			print("[XCF] Tmdb: ", str(e))
		return True

	elif Utils.is_imdb:
		try:
			from Plugins.Extensions.IMDb.plugin import main as imdb
			imdb(_session, text)
		except Exception as e:
			print("[XCF] imdb: ", str(e))
		return True
	else:
		_session.open(MessageBox, text, MessageBox.TYPE_INFO)
		return True
	return False


def get_rtmp(data):
	try:
		from urllib3.exceptions import InsecureRequestWarning
		from urllib3 import disable_warnings
		disable_warnings(InsecureRequestWarning)
		referer = 'http://www.filmon.com'
		from .lib import client
		headers = {'User-Agent': client.agent(), 'Referer': referer}
		content = six.ensure_str(client.request(data, headers=headers))
		rtmp = findall(r'"quality".*?url"\:"(.*?)"', content)
		if rtmp:
			fin_url = rtmp[0].replace('\\', '')
			return fin_url
	except Exception as ex:
		print("Error: can't read data", ex)
		return None


def get_session():
	urlx = 'http://www.filmon.com/tv/api/init?app_android_device_model=GT-N7000&app_android_test=false&app_version=2.0.90&app_android_device_tablet=true&app_android_device_manufacturer=SAMSUNG&app_secret=wis9Ohmu7i&app_id=android-native&app_android_api_version=10%20HTTP/1.1&channelProvider=ipad&supported_streaming_protocol=rtmp'
	req = Request(urlx)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
	req.add_header('Referer', 'http://www.filmon.com/')
	req.add_header('X-Requested-With', 'XMLHttpRequest')
	try:
		page = urlopen(req, None, 15)
		content = page.read()
		if PY3:
			content = six.ensure_str(content)

		x = json_loads(content)
		session = x.get("session_key", 'none')
		if session != 'none':
			return str(session)
		else:
			return 'none'
	except HTTPError as e:
		print("HTTP error occurred: {} - {}".format(e.code, e.reason))
	except URLError as e:
		print("URL error occurred: {}".format(e.reason))
	except Exception as e:
		print("An unexpected error occurred: {}".format(e))
	return 'none'


class filmon(Screen):
	def __init__(self, session):
		self.session = session
		skin = skin_path
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()
		Screen.__init__(self, session)
		global _session
		_session = session
		self.menulist = []
		self.setTitle(title_plug)
		self['menulist'] = m2list([])
		self['red'] = Label(_('Exit'))
		self['yellow'] = Label(_('Update'))
		self['name'] = Label('Loading data... Please wait')
		self['text'] = Label()
		self['poster'] = Pixmap()
		self.picload = ePicLoad()
		self.currentList = 'menulist'
		# self.currentList = self['menulist']
		self.Update = False
		self["actions"] = ActionMap(
			[
				"ChannelSelectBaseActions",
				"DirectionActions",
				"HotkeyActions",
				"InfobarEPGActions",
				"OkCancelActions",
			],
			{
				"cancel": self.closerm,
				"down": self.down,
				"green": self.ok,
				"info_long": self.update_dev,
				"infolong": self.update_dev,  # alias? mantenuto se serve compatibilità
				"left": self.left,
				"ok": self.ok,
				"red": self.closerm,
				"right": self.right,
				"showEventInfoPlugin": self.update_dev,
				"up": self.up,
				"yellow": self.update_me,
				"yellow_long": self.update_dev,
			},
			-1
		)

		self.timer = eTimer()
		if exists('/var/lib/dpkg/status'):
			self.timer_conn = self.timer.timeout.connect(self.check_vers)
		else:
			self.timer.callback.append(self.check_vers)
		self.timer.start(500, 1)
		self.onLayoutFinish.append(self.downxmlpage)

	def check_vers(self):
		"""
		Check the latest version and changelog from the remote installer URL.
		If a new version is available, notify the user.
		"""
		remote_version = '0.0'
		remote_changelog = ''
		try:

			def feth(url):
				try:
					req = Request('http://example.com')
					response = urlopen(req)
					content = response.read()
					response.close()
					return content
				except HTTPError as e:
					print('Errore HTTP: %s' % str(e))
				except URLError as e:
					print('Errore URL: %s' % str(e))
				except Exception as e:
					print('Errore generico: %s' % str(e))
				return None

			req = Utils.Request(Utils.b64decoder(installer_url), headers={'User-Agent': 'Mozilla/5.0'})
			page = Utils.urlopen(req).read()
			page = feth(installer_url)
			data = page.decode("utf-8") if PY3 else page.encode("utf-8")
			if data:
				lines = data.split("\n")
				for line in lines:
					if line.startswith("version"):
						remote_version = line.split("'")[1] if "'" in line else '0.0'
					elif line.startswith("changelog"):
						remote_changelog = line.split("'")[1] if "'" in line else ''
						break
		except Exception as e:
			self.session.open(MessageBox, _('Error checking version: %s') % str(e), MessageBox.TYPE_ERROR, timeout=5)
			return
		self.new_version = remote_version
		self.new_changelog = remote_changelog
		# if float(currversion) < float(remote_version):
		if currversion < remote_version:
			self.Update = True
			self.session.open(
				MessageBox,
				_('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') % (self.new_version, self.new_changelog),
				MessageBox.TYPE_INFO,
				timeout=5
			)

	def update_me(self):
		if self.Update is True:
			self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (self.new_version, self.new_changelog), MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

	def update_dev(self):
		try:
			req = Utils.Request(Utils.b64decoder(developer_url), headers={'User-Agent': 'Mozilla/5.0'})
			page = Utils.urlopen(req).read()
			data = json_loads(page)
			remote_date = data['pushed_at']
			strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
			remote_date = strp_remote_date.strftime('%Y-%m-%d')
			self.session.openWithCallback(self.install_update, MessageBox, _("Do you want to install update ( %s ) now?") % (remote_date), MessageBox.TYPE_YESNO)
		except Exception as e:
			print('error xcons:', e)

	def install_update(self, answer=False):
		if answer:
			cmd1 = 'wget -q "--no-check-certificate" ' + Utils.b64decoder(installer_url) + ' -O - | /bin/sh'
			self.session.open(xConsole, 'Upgrading...', cmdlist=[cmd1], finishedCallback=self.myCallback, closeOnSuccess=False)
		else:
			self.session.open(MessageBox, _("Update Aborted!"),  MessageBox.TYPE_INFO, timeout=3)

	def myCallback(self, result=None):
		print('result:', result)
		return

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
		self.auswahl = ''
		self.index = 'group'
		self.cat_list = []
		global sessionx
		sessionx = get_session()
		url = data
		if PY3:
			url = six.ensure_str(url)
		# print("content 3 =", url)
		try:
			n1 = url.find('<ul class="group-channels"', 0)
			n2 = url.find('<div id="footer">', n1)
		except:
			n1 = url.find(b'<ul class="group-channels"', 0)
			n2 = url.find(b'<div id="footer">', n1)
		url = url[n1:n2]
		regexvideo = 'class="group-item".*?a href="(.*?)".*?logo" src="(.*?)".*?title="(.*?)"'
		#  regexvideo = '<li class="group-item".*?a href="(.*?)".*?title="(.*?)"'
		match = compile(regexvideo, DOTALL).findall(url)
		for url, img, name in match:
			img = img.replace('\\', '')
			url = "http://www.filmon.com" + url
			# pic = ''
			url = Utils.checkStr(url)
			img = Utils.checkStr(img)
			name = Utils.checkStr(name)
			self.cat_list.append(show_(name, url, img, sessionx, name))
		self['menulist'].l.setList(self.cat_list)
		self['menulist'].moveToIndex(0)
		self['name'].setText('Select')
		self.auswahl = self['menulist'].getCurrent()[0][0]
		self['name'].setText(self.auswahl)
		# self['text'].setText()
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
		try:
			n1 = r.find('channels"', 0)
			n2 = r.find('channels_count"', n1)
		except:
			n1 = r.find('channels"', 0)
			n2 = r.find('channels_count"', n1)
		r2 = r[n1:n2]
		channels = findall('"id":(.*?),"logo":".*?","big_logo":"(.*?)","title":"(.*?)",.*?description":"(.*?)"', r2)
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

		self.xcurrentList = [(item[0], item[1]) for item in self.cat_list]
		# print('xcurrentList=', self.xcurrentList)

		self.auswahl = self['menulist'].getCurrent()[0][0]
		self['name'].setText(str(self.auswahl))
		self.load_poster()

	def ok(self):
		try:
			if self.index == 'cat':
				id = self['menulist'].getCurrent()[0][1]
				session = self['menulist'].getCurrent()[0][3]
				url = 'http://www.filmon.com/api-v2/channel/' + str(id) + "?session_key=" + session
				# print("url OK", url)
				self.get_rtmpi(url)
			elif self.index == 'group':
				url = self['menulist'].getCurrent()[0][1]
				session = self['menulist'].getCurrent()[0][3]
				self.cat(url)
		except Exception as e:
			print("Error: can't find file", e)

	def get_rtmpi(self, data):
		try:
			fin_url = get_rtmp(data)
			selected_item = self['menulist'].getCurrent()
			i = self['menulist'].getSelectedIndex()
			selection = self['menulist'].l.getCurrentSelection()
			item = selected_item[i]
			name = item[0]
			url = item[1]
			self.currentindex = i
			if selection is not None:
				url = fin_url
				# print("name:", name, "url:", url)
				self.play_that_shit(url, name, self.currentindex, item, self.xcurrentList)
		except Exception as ex:
			print("Error: can't read data", ex)

	def play_that_shit(self, url, name, index, item, xcurrentList):
		self.session.open(Playstream2, name, url, index, item, xcurrentList)

	def closerm(self):
		if self.index == 'group':
			Utils.deletetmp()
			self.close()
		elif self.index == 'cat':
			self.downxmlpage()

	def load_poster(self):
		global tmp_image
		if self.index == 'cat':
			descriptionX = self['menulist'].getCurrent()[0][4]
			self['text'].setText(descriptionX)

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
						downloadPage(pixmaps, tmp_image, sniFactory, timeout=5).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
					else:
						downloadPage(pixmaps, tmp_image).addCallback(self.downloadPic, tmp_image).addErrback(self.downloadError)
				except Exception as ex:
					print("Error: can't find file or read data", ex)
			return

	def downloadPic(self, data, pictmp):
		if exists(pictmp):
			try:
				self.poster_resize(pictmp)
			except Exception as ex:
				print("* error ** %s" % ex)
				pass
			except:
				pass

	def downloadError(self, png):
		try:
			if exists(png):
				self.poster_resize(tmp_image)
		except Exception as ex:
			self.poster_resize(tmp_image)
			print('exe downloadError', ex)

	def poster_resize(self, png):
		self["poster"].hide()
		if exists(png):
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
			return


class TvInfoBarShowHide():
	STATE_HIDDEN = 0
	STATE_HIDING = 1
	STATE_SHOWING = 2
	STATE_SHOWN = 3
	FLAG_CENTER_DVB_SUBS = 2048
	skipToggleShow = False

	def __init__(self):
		self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"],
											{"toggleShow": self.OkPressed,
											 "hide": self.hide}, 0)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evStart: self.serviceStarted})
		self.__state = self.STATE_SHOWN
		self.__locked = 0
		self.hideTimer = eTimer()
		try:
			self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
		except AttributeError:
			self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(3000, True)
		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)

	def OkPressed(self):
		self.toggleShow()

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		self.startHideTimer()

	def __onHide(self):
		self.__state = self.STATE_HIDDEN

	def serviceStarted(self):
		if self.execing:
			self.doShow()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN and not self.__locked:
			self.hideTimer.stop()
			self.hideTimer.start(3000, True)
		elif hasattr(self, "pvrStateDialog"):
			self.hideTimer.stop()
		self.skipToggleShow = False

	def doShow(self):
		self.hideTimer.stop()
		self.show()
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		if self.__state == self.STATE_SHOWN:
			self.hide()

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

	def lockShow(self):
		self.__locked += 1
		if self.execing:
			self.show()
			self.hideTimer.stop()
			self.skipToggleShow = False

	def unlockShow(self):
		self.__locked = max(0, self.__locked - 1)
		if self.__locked == 0 and self.execing:
			self.startHideTimer()


class Playstream2(InfoBarBase,
				  InfoBarMenu,
				  InfoBarSeek,
				  InfoBarAudioSelection,
				  InfoBarNotifications,
				  TvInfoBarShowHide,
				  Screen):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
	screen_timeout = 5000

	def __init__(self, session, name, url, index, item, currentList):

		global streaml, _session
		Screen.__init__(self, session)
		self.session = session
		_session = session
		self.skinName = 'MoviePlayer'
		self.currentindex = index
		self.item = item
		self.itemscount = len(currentList)
		self.list = currentList
		streaml = False
		for x in InfoBarBase, \
				InfoBarMenu, \
				InfoBarSeek, \
				InfoBarAudioSelection, \
				InfoBarNotifications, \
				TvInfoBarShowHide:
			x.__init__(self)
		self.allowPiP = False
		self.service = None
		self.url = url
		self.name = html_conv.html_unescape(name)
		self.state = self.STATE_PLAYING
		self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
		self['actions'] = ActionMap(
			[
				'ButtonSetupActions',
				'ChannelSelectBaseActions',
				'ColorActions',
				'DirectionActions',
				'EPGSelectActions',
				'InfobarActions',
				'InfobarSeekActions',
				'InfobarShowHideActions',
				'MediaPlayerActions',
				'MediaPlayerSeekActions',
				'MoviePlayerActions',
				'MovieSelectionActions',
				'OkCancelActions',
			],
			{
				'epg': self.showIMDB,
				'info': self.showIMDB,
				'stop': self.cancel,
				'leavePlayer': self.cancel,
				'back': self.cancel,
				'prevBouquet': self.previousitem,
				'nextBouquet': self.nextitem,
				'channelDown': self.previousitem,
				'channelUp': self.nextitem,
				'down': self.previousitem,
				'up': self.nextitem,
				'cancel': self.cancel,
			},
			-1
		)

		if '8088' in str(self.url):
			streaml = True
			self.onFirstExecBegin.append(self.slinkPlay)
		else:
			self.onFirstExecBegin.append(self.openTest)
		self.onClose.append(self.cancel)

	def nextitem(self):
		# Increment the current index
		currentindex = int(self.currentindex) + 1
		# print("nextitem currentindex:", currentindex)
		# Circular handling
		if currentindex >= len(self.list):
			currentindex = 0  # Go back to the beginning
		# print("nextitem currentindex after check:", currentindex)
		# Update the current index and call update_channel
		self.currentindex = currentindex
		self.update_channel()

	def previousitem(self):
		# Decrement the current index
		currentindex = int(self.currentindex) - 1
		# print("previousitem currentindex:", currentindex)
		# Circular handling: go back to the last item if going past the beginning
		if currentindex < 0:
			currentindex = len(self.list) - 1  # Go to the last item
		# print("previousitem currentindex after check:", currentindex)
		# Update the current index and call update_channel
		self.currentindex = currentindex
		self.update_channel()

	def update_channel(self):
		if not self.list:
			# print("Error: the list is empty")
			return
		if self.currentindex >= len(self.list) or self.currentindex < 0:
			# print("Error: index out of range")
			return
		group = self.list[self.currentindex]
		# print('group=', group)
		self.url = None
		# print("Group content:", group)
		session = group[0][3]
		# print("Session Key:", session)
		self.name = group[0][0]
		# print("self.name:", self.name)
		id = group[0][1]
		if session and id:
			url = 'http://www.filmon.com/api-v2/channel/' + str(id) + "?session_key=" + session
			self.url = get_rtmp(url)
			# print("url OK player", self.url)

		if self.url is not None:
			self.openTest()
		else:
			print("Error: URL not found")

	def openTest(self):
		servicetype = '4097'
		name = self.name
		url = self.url
		if url:
			ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
			# print('reference:   ', ref)
			if streaml is True:
				url = 'http://127.0.0.1:8088/' + str(url)
				ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
			# print('final reference:   ', ref)
			sref = eServiceReference(ref)
			sref.setName(name)
			self.session.nav.stopService()
			self.session.nav.playService(sref)
		else:
			print("Errore: URL non valido in openTest()")

	def doEofInternal(self, playing):
		# print('doEofInternal', playing)
		Utils.MemClean()
		if self.execing and playing:
			self.openTest()

	def __evEOF(self):
		# print('__evEOF')
		self.end = True
		Utils.MemClean()
		self.openTest()

	def showIMDB(self):
		text_clear = self.name
		if returnIMDB(text_clear):
			print('show imdb/tmdb')

	def slinkPlay(self):
		name = self.name
		url = self.url
		ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
		# print('final reference:   ', ref)
		sref = eServiceReference(ref)
		sref.setName(str(name))
		self.session.nav.stopService()
		self.session.nav.playService(sref)

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
		# print('reference youtube:   ', ref)
		sref = eServiceReference(ref)
		sref.setName(str(name))
		self.session.nav.stopService()
		self.session.nav.playService(sref)

	def showAfterSeek(self):
		if isinstance(self, TvInfoBarShowHide):
			self.doShow()

	def cancel(self):
		if exists('/tmp/hls.avi'):
			remove('/tmp/hls.avi')
		self.session.nav.stopService()
		self.session.nav.playService(self.srefInit)
		aspect_manager.restore_aspect()
		self.close()

	def leavePlayer(self):
		self.cancel()


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
	result = [PluginDescriptor(name=title_plug, description=desc_plugin, where=PluginDescriptor.WHERE_PLUGINMENU, icon=icona, fnc=main)]
	result.append(extDescriptor)
	return result
	# PluginDescriptor(name=title_plug, description=desc_plugin, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
