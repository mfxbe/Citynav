#!/usr/bin/env python3
# Import flet and systems libraries
import asyncio
import flet as ft

from settings import *
import json
from urllib.request import urlopen


def station_getter(lat, lon):
	url = "https://www.mvg.de/api/bgw-pt/v3/stations/nearby?latitude=" + lat + "&longitude=" + lon
	response = urlopen(url)
	jData = json.loads(response.read())
	return jData[0]["name"]

def stop_pos_finder(d, curSe):
	if "platform" in d and curSe["settings"].stops_shown:
		platformContainer = ft.Container(
			ft.Text(d["platform"], text_align=ft.TextAlign.CENTER, size=8, color=ft.Colors.ON_SECONDARY_CONTAINER,
			        no_wrap=True),
			alignment=ft.alignment.center,
			width=8,
			height=15,
			bgcolor=ft.Colors.SECONDARY_CONTAINER
		)
	elif "stopPositionNumber" in d and curSe["settings"].stops_shown:
		platformContainer = ft.Container(
			ft.Text(d["stopPositionNumber"], text_align=ft.TextAlign.CENTER, size=8,
			        color=ft.Colors.ON_SECONDARY_CONTAINER, no_wrap=True),
			alignment=ft.alignment.center,
			width=8,
			height=15,
			bgcolor=ft.Colors.SECONDARY_CONTAINER
		)
	else:
		platformContainer = ft.Text(" ",
									size=8)  # empty text field as placeholder if there is no platform or show is of

	return platformContainer


class MyPage(ft.AnimatedSwitcher):
	def __init__(self, header, curSe):
		super().__init__(ft.Text(""))
		self.pages = dict()
		self.ct = None
		self.header = header
		self.curSe = curSe
		self.currentParent = None

	def switched(self):
		pass

	def did_mount(self):
		self.navbar_helper(self.pages[self.ct].my_page_parent)
		self.update()
		self.switch_sub(self.ct)
		self.page.update()

	def switch_sub(self, title, notify=True):
		self.ct = title
		self.content = self.pages[title]
		self.currentParent = self.pages[title].my_page_parent
		self.navbar_helper(self.pages[title].my_page_parent)
		if notify:
			self.switched()

	def add_sub(self, title, content, parent=None):
		if self.curSe["page"].platform == ft.PagePlatform.ANDROID or self.curSe["page"].platform == ft.PagePlatform.IOS:
			container = ft.Row([ft.Container(content, expand=True, padding=0, margin=0)], expand=True, spacing=0)
		else:
			# handle display of navigation rail for desktop
			container = ft.Row([self.curSe["mainView"].rail, ft.VerticalDivider(width=1),
								ft.Container(content, expand=True, padding=0, margin=0)], expand=True, spacing=0)

		container.my_page_parent = parent
		self.pages[title] = container
		if self.ct is None: self.ct = title

	def navbar_helper(self, parent):
		if self.page is not None:
			if parent is None:
				backButton = None
				lw = 10
			else:
				lw = 40
				backButton = ft.IconButton(ft.Icons.ARROW_BACK)
				backButton.on_click = lambda e: self.switch_sub(parent)

			self.parent.parent.appbar = ft.AppBar(
				automatically_imply_leading=False,
				leading_width=lw,
				leading=backButton,
				title=ft.GestureDetector(content=ft.WindowDragArea(content=ft.Text(self.header), width=2000), mouse_cursor=ft.MouseCursor.MOVE), #expand=True doesn't work so use high number here (seems to have no negative effects); gesture controller to allow changing style of mouse
				bgcolor="#36618e",
				color="white",
				actions=[
					ft.IconButton(ft.Icons.MORE_VERT, on_click=lambda e, p=self.page: page_settings(p, self.curSe))
				]
			)

			def close_app(_e):
				self.page.window.close()

			if self.page.platform is not ft.PagePlatform.ANDROID and self.page.platform is not ft.PagePlatform.IOS and self.page.web is False:
				self.parent.parent.appbar.actions.append(ft.IconButton(ft.Icons.CLOSE, on_click=lambda _e: close_app(_e)))

			self.page.update()


def color_allocator(line):
	color = None
	fixed = {"U1": "#3c7333", "U2": "#c3022d", "U3": "#ed6720", "U4": "#00ab85", "U5": "#bd7b00", "U6": "#0065b0",
			 "U7": "#c0ba79", "U8": "#c53f09",
			 "S1": "#0ec1ea", "S2": "#72c042", "S3": "#7c087e", "S4": "#ef1620", "S5": "#046a89", "S6": "#008b50",
			 "S7": "#973530", "S8": "#2d2b29", "S20": "#f15a74", "SEV": "#95368c"}

	if line.isdigit():
		dLine = int(line)
		if dLine < 40:
			color = "#d91a1a"
		else:
			color = "#00576a"
	elif line in fixed:
		color = fixed[line]
	elif line[:2] in fixed:
		color = fixed[line[:2]]
	elif line.startswith("N"):
		if int(line.replace("N", "")) < 40:
			color = "#d91a1a"
		else:
			color = "#00576a"
	elif line.startswith("X"):
		color = "#00576a"
	elif line.startswith("RB") or line.startswith("RE"):
		color = "#000000"
	else:
		color = "#aeaeaf"

	return color


class StorageHandler():
	def __init__(self, page):
		self.p = page
		self.prefix = "de.mfxbe.Citynav."

		# defaults if everything in set_up fails
		self.theme = "auto"
		self.results = 1
		self.connection_history = ""
		self.departures_history = ""
		self.default = 0
		self.language = "unset"
		self.stops_shown = False
		self.messages_show = "current"

	async def set_up(self):
		# Set defaults

		try:
			self.theme = await self.set_from_storage("theme", "auto")
			self.results = await self.set_from_storage("results", 1)
			self.connection_history = await self.set_from_storage("connection_history", "")
			self.departures_history = await self.set_from_storage("departures_history", "")
			self.default = await self.set_from_storage("default", 0)
			self.language = await self.set_from_storage("language", "unset")
			self.stops_shown = await self.set_from_storage("stops_shown", False)
			self.messages_show = await self.set_from_storage("messages_show", "current")
		except Exception as e:
			print(e)
			snBar = ft.SnackBar(ft.Text(f"Fehler beim Setzten von Nutzereinstellungen"))
			self.p.overlay.append(snBar)
			snBar.open = True
			self.p.update()

	def set_key(self, key, value):
		#here a trick is needed because the "correct" way of loading the data from storage doesnt work in web
		try:
			loop = asyncio.get_event_loop()
			loop.create_task( self.p._invoke_method_async( # noqa: WPS437
			"clientStorage:set",
				{"key": self.prefix + key, "value": str(value)},
				wait_timeout=10,
			) )
		except RuntimeError as e:
			asyncio.run( self.p._invoke_method_async( # noqa: WPS437
				"clientStorage:set",
				{"key": self.prefix + key, "value": str(value)},
				wait_timeout=10,
			) )

		# following is the "normal way"
		# this would show a timeout error on web (but does indeed work despite that) but it takes for ever
		# see also set_from_storage and https://github.com/flet-dev/flet/issues/3783
		# try:
		# 	self.p.client_storage.set(self.prefix + key, value)
		# except:
		# 	pass
		setattr(self, key, value)

	def get_key(self, key):
		value = self.p.client_storage.get(self.prefix + key)
		return value

	async def set_from_storage(self, key, default):
		result = default

		#here a trick is needed because the "correct" way of loading the data from storage doesnt work in web
		token = await self.p._invoke_method_async(
			method_name="clientStorage:get",
			arguments={"key": self.prefix + key},
			wait_timeout=10,
			wait_for_result=True,
		)
		if token is not None:
			result = await self.p._invoke_method_async(  # noqa: WPS437
				method_name="clientStorage:get",
				arguments={"key": self.prefix + key},
				wait_timeout=10,
				wait_for_result=True,
			)

			# the data saved to client storage somehow gets a bit "corrupted" fixing this manually here
			if "history" not in key:
				result = result.replace("\"", "")
				result = result.replace("\\", "")
			else:
				result = result.replace("\\", "")
				result = result[1:-1]

			if result == "True": result = True
			if result == "False": result = False
			if key == "results": result = int(result[0])

		#this is the code that should work but doesn't see: https://github.com/flet-dev/flet/issues/3783
		##if self.p.client_storage.contains_key(self.prefix + key) or self.p.client_storage.get(
		##		self.prefix + key) is not None:
		##	result = self.p.client_storage.get(self.prefix + key)
		# NOTE TO ME: if ever switching back to this way, also change a lot of settings stuff on other places because then
		# all types are easily possible again not just strings like in the workaround above

		return result

	def reset_all(self):
		appKeys = self.p.client_storage.get_keys(self.prefix + "")
		for k in appKeys:
			self.p.client_storage.remove(k)
