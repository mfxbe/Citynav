#!/usr/bin/env python3
# Import flet and systems libraries
import json
from datetime import datetime
from urllib.request import urlopen

import flet as ft

# Import other parts of this app
import StationSearchBar
from common import MyPage, color_allocator


class DeparturePage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__("Abfahrten")
		self.curSe = curSe

		# Page structure of startPage
		startPage = ft.Column()
		positionSearchBar = StationSearchBar.StationSearchBar(hint="Haltestelle", stations=curSe["stops"])
		startPage.controls.append(ft.Container(positionSearchBar, alignment=ft.alignment.center))
		goButton = ft.FilledButton(text="Abfahrten anzeigen", expand=True,
								   style=ft.ButtonStyle(bgcolor="#36618e", color="white"))
		self.goButton = goButton
		startPage.controls.append(ft.Row(controls=[goButton]))
		startPage.controls.append(ft.Row())
		historyHeader = ft.Text("Verlauf", weight=ft.FontWeight.BOLD)
		startPage.controls.append(ft.Row(controls=[historyHeader]))

		self.add_sub("startPage", ft.Container(startPage, padding=10))

		def do_action(e):
			curSe["position"] = positionSearchBar.value
			curSe["positionID"] = None

			for s in curSe["stops"]:
				if s["name"] == curSe["position"]:
					curSe["positionID"] = s["id"]
					break

			if curSe["positionID"] is not None:
				goButton.content = ft.ProgressRing(width=14, height=14, color=ft.colors.ON_PRIMARY, stroke_width=2)
				self.goButton.update()
				self.display_result_page()
			else:
				curSe["page"].snack_bar = ft.SnackBar(ft.Text("Unbekannte Haltestelle"))
				curSe["page"].snack_bar.open = True
				curSe["page"].update()

		goButton.on_click = do_action

		# detailsPage (basics more see display_result_page)
		self.detailsPage = ft.Column()
		self.add_sub("detailsPage", ft.Container(self.detailsPage, padding=10, expand=True), "startPage")

	def display_result_page(self):
		curSe = self.curSe
		listview = ft.ListView()
		listview.expand = True
		self.detailsPage.controls.clear()
		self.detailsPage.controls.append(listview)
		self.detailsPage.expand = True

		if curSe["settings"].results == 0:
			resultLimit = 10
		elif curSe["settings"].results == 1:
			resultLimit = 20
		else:
			resultLimit = 30

		try:
			response = urlopen(
				"https://www.mvg.de/api/fib/v2/departure?limit=" + str(resultLimit) + "&offsetInMinutes=0&globalId=" +
				curSe[
					"positionID"])
			departures = json.loads(response.read())
		except:
			self.switch_sub("startPage")
			self.page.snack_bar = ft.SnackBar(ft.Text(f"Fehler beim Datenabruf"))
			self.page.snack_bar.open = True
			self.page.update()
		else:
			for d in departures:
				timedelta = datetime.fromtimestamp(d["realtimeDepartureTime"] / 1000) - datetime.now()
				timedeltaValue = round(timedelta.total_seconds() / 60)
				if timedeltaValue < 0: continue

				lineColor = color_allocator(d["label"])
				if d["label"].startswith("S"):
					cont = ft.Container(ft.Text(d["label"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
										alignment=ft.alignment.center, border_radius=10)
				else:
					cont = ft.Container(ft.Text(d["label"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
										alignment=ft.alignment.center)

				entry = ft.Row([
					ft.Row([
						cont,
						ft.Text(d["destination"])
					]),
					ft.Text(str(timedeltaValue) + " Min")
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				listview.controls.append(entry)
				listview.controls.append(ft.Divider())

		self.switch_sub("detailsPage")
		self.update()

	def switched(self):
		# Reset the loading button when returning to startPage
		if self.goButton.page is not None:
			self.goButton.content = ft.Text("Abfahrten anzeigen")
			self.goButton.update()
