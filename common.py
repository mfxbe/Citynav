#!/usr/bin/env python3
# Import flet and systems libraries
import flet as ft
from settings import *

def stop_pos_finder(d):
	if "platform" in d:
		platformContainer = ft.Container(
			ft.Text(d["platform"], text_align=ft.TextAlign.CENTER, size=8, color=ft.colors.ON_SECONDARY_CONTAINER),
			alignment=ft.alignment.center,
			width=8,
			height=15,
			bgcolor=ft.colors.SECONDARY_CONTAINER
		)
	elif "stopPositionNumber" in d:
		platformContainer = ft.Container(
			ft.Text(d["stopPositionNumber"], text_align=ft.TextAlign.CENTER, size=8, color=ft.colors.ON_SECONDARY_CONTAINER),
			alignment=ft.alignment.center,
			width=8,
			height=15,
			bgcolor=ft.colors.SECONDARY_CONTAINER
		)
	else:
		platformContainer = ft.Text(" ", size=8) #empty text field as placeholder if there is no platform

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
				backButton = ft.IconButton(ft.icons.ARROW_BACK)
				backButton.on_click = lambda e: self.switch_sub(parent)

			self.parent.parent.appbar = ft.AppBar(
				automatically_imply_leading=False,
				leading_width=lw,
				leading=backButton,
				title=ft.Text(self.header),
				bgcolor="#36618e",
				color="white",
				actions=[
					ft.IconButton(ft.icons.MORE_VERT, on_click=lambda e, p=self.page: page_settings(p, self.curSe))]
			)

			self.page.update()


def color_allocator(line):
	color = None
	fixed = {"U1": "#3c7333", "U2": "#c3022d", "U3": "#ed6720", "U4": "#00ab85", "U5": "#bd7b00", "U6": "#0065b0",
			 "U7": "#c0ba79", "U8": "#c53f09",
			 "S1": "#0ec1ea", "S2": "#72c042", "S3": "#7c087e", "S4": "#ef1620", "S5": "#ffcd00", "S6": "#008b50",
			 "S7": "#973530", "S8": "#000000", "S20": "#f15a74"}

	if line.isdigit():
		dLine = int(line)
		if dLine < 40:
			color = "#d91a1a"
		else:
			color = "#00576a"
	elif line in fixed:
		color = fixed[line]
	elif line.startswith("N"):
		if int(line.replace("N", "")) < 40:
			color = "#d91a1a"
		else:
			color = "#00576a"
	elif line.startswith("X"):
		color = "#00576a"
	else:
		color = "#aeaeaf"

	return color


class StorageHandler():
	def __init__(self, page):
		self.p = page
		self.prefix = "de.mfxbe.Citynav."

		# Set defaults
		try:
			self.theme = self.set_from_storage("theme", "auto")
			self.results = self.set_from_storage("results", 1)
			self.connection_history = self.set_from_storage("connection_history", list())
			self.departures_history = self.set_from_storage("departures_history", list())
			self.default = self.set_from_storage("default", 0)
		except Exception as e:
			print(e)

			self.theme = "auto"
			self.results = 1
			self.connection_history = list()
			self.departures_history = list()
			self.default = 0

			self.p.snack_bar = ft.SnackBar(ft.Text(f"Fehler beim Setzten von Nutzereinstellungen"))
			self.p.snack_bar.open = True
			self.p.update()

	def set_key(self, key, value):
		self.p.client_storage.set(self.prefix + key, value)
		setattr(self, key, value)

	def get_key(self, key):
		value = self.p.client_storage.get(self.prefix + key)
		return value

	def set_from_storage(self, key, default):
		result = default

		if self.p.client_storage.contains_key(self.prefix + key) or self.p.client_storage.get(
				self.prefix + key) is not None:
			result = self.p.client_storage.get(self.prefix + key)

		return result

	def reset_all(self):
		appKeys = self.p.client_storage.get_keys(self.prefix + "")
		for k in appKeys:
			self.p.client_storage.remove(k)
