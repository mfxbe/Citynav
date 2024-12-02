#!/usr/bin/env python3
# Import flet and systems libraries
import flet as ft
from difflib import SequenceMatcher

from locales import _

class StationSearchBar(ft.SearchBar):
	def __init__(self, hint, stations):
		super().__init__()
		self.stations = []
		self.lv = ft.ListView()

		searchPositionButton = ft.IconButton(icon=ft.Icons.LOCATION_ON_OUTLINED)
		self.searchPositionButton = searchPositionButton

		self.stations = stations
		self.bar_bgcolor = ft.Colors.ON_TERTIARY
		self.bar_trailing = [searchPositionButton]
		self.view_hint_text = _("Haltestelle")
		self.bar_hint_text = hint
		self.controls = [self.lv]
		self.on_tap = lambda e: self.open_view()
		self.on_change = self.handle_change

		index = 0
		for i in self.stations:
			y = i["name"]
			self.lv.controls.append(ft.ListTile(title=ft.Text(f"{y}"), on_click=self.close_anchor, data=y))
			index = index + 1
			if index >= 30:
				break

	def handle_change(self, e):
		self.lv.controls.clear()

		searchTerm = e.data

		if searchTerm == "hbf" or searchTerm == "Hbf":
			searchTerm = "Hauptbahnhof"

		if searchTerm == "":
			index = 0
			for i in self.stations:
				y = i["name"]
				self.lv.controls.append(ft.ListTile(title=ft.Text(f"{y}"), on_click=self.close_anchor, data=y))
				index = index + 1
				if index >= 30:
					break
		else:
			index = 0
			for i in self.stations:
				y = i["name"]
				if searchTerm.lower() in y.lower():
					self.lv.controls.append(ft.ListTile(title=ft.Text(f"{y}"), on_click=self.close_anchor, data=y))
					index = index + 1
					if index >= 30:
						break

			if index < 1:
				for i in self.stations:
					y = i["name"]
					if SequenceMatcher(None, searchTerm.lower(), y.lower()).ratio() > 0.8:
						self.lv.controls.append(ft.ListTile(title=ft.Text(f"{y}"), on_click=self.close_anchor, data=y))
						index = index + 1
						if index >= 30:
							break

		self.lv.update()

	def close_anchor(self, e):
		selected_item = e.control.data
		self.close_view(selected_item)
