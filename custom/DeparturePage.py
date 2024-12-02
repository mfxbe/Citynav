#!/usr/bin/env python3
# Import flet and systems libraries
import asyncio
import json
import time
from datetime import datetime
from urllib.request import urlopen

import flet as ft

# Import other parts of this app
from locales import _
from custom import StationSearchBar
from common import MyPage, color_allocator, stop_pos_finder


class DeparturePage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__(_("Departures"), curSe)
		self.curSe = curSe

		# Page structure of startPage
		startPage = ft.Column()
		positionSearchBar = StationSearchBar.StationSearchBar(hint=_("Stop"), stations=curSe["stops"])
		startPage.controls.append(ft.Container(positionSearchBar, alignment=ft.alignment.center))
		goButton = ft.FilledButton(text=_("Search departures"), expand=True,
								   style=ft.ButtonStyle(bgcolor="#36618e", color="white"))
		self.goButton = goButton
		startPage.controls.append(ft.Row(controls=[goButton]))
		startPage.controls.append(ft.Row())
		historyHeader = ft.Text(_("History"), weight=ft.FontWeight.BOLD)
		startPage.controls.append(ft.Row(controls=[historyHeader]))

		historyElms = list()
		def toggle_star_button(e):
			e.control.selected = not e.control.selected
			e.control.update()
			e.control.d["star"] = e.control.selected
			curSe["settings"].set_key("departures_history", json.dumps(historyElms, ensure_ascii=False))

		def history_clicked(fromSta):
			positionSearchBar.value = fromSta
			positionSearchBar.update()

		historyListView = ft.ListView(controls=[], divider_thickness=1, spacing=5, padding=ft.padding.only(left=10, right=10))
		startPage.controls.append(historyListView)
		def process_history():
			nonlocal historyElms
			if curSe["settings"].departures_history != "":
				historyElms = json.loads(curSe["settings"].departures_history)
				historyElms = sorted(historyElms, key=lambda se: (-se["star"], -se["latest"]))
				while len(historyElms) > 7:
					historyElms.pop()
				curSe["settings"].set_key("departures_history", json.dumps(historyElms, ensure_ascii=False))

				historyListView.controls = []
				for e in historyElms:
					container1 = ft.Text(e["station"])
					container4 = ft.Container(expand=True)
					container5 = ft.IconButton(selected=e["star"], icon=ft.Icons.STAR_BORDER, selected_icon=ft.Icons.STAR, on_click=toggle_star_button)
					container5.d = e
					containerRow = ft.Row(controls=[container1,  container4, container5])
					historyListView.controls.append(ft.GestureDetector(containerRow, mouse_cursor=ft.MouseCursor.CLICK, on_tap=(lambda _d, f=e: (history_clicked(f["station"])))))
		process_history()

		self.add_sub("startPage", ft.Container(startPage, padding=10))

		def do_action(e):
			curSe["position"] = positionSearchBar.value
			curSe["positionID"] = None

			for s in curSe["stops"]:
				if s["name"] == curSe["position"]:
					curSe["positionID"] = s["id"]
					break

			if curSe["positionID"] is not None:
				goButton.content = ft.ProgressRing(width=14, height=14, color=ft.Colors.ON_PRIMARY, stroke_width=2)
				self.goButton.update()

				# add to history
				found = False
				for e in historyElms:
					if e["station"] == positionSearchBar.value:
						found = True
						e["latest"] = time.time()
				if not found:
					d = {"station": positionSearchBar.value, "latest": time.time(), "star": False}
					historyElms.append(d)
				curSe["settings"].set_key("departures_history", json.dumps(historyElms, ensure_ascii=False))
				process_history()


				self.display_result_page()
			else:
				snBar = ft.SnackBar(ft.Text(_("Unknown stop")))
				curSe["page"].overlay.append(snBar)
				snBar.open = True
				curSe["page"].update()

		goButton.on_click = do_action

		# detailsPage (basics more see display_result_page)
		self.detailsPage = ft.Column(expand=True)
		self.add_sub("detailsPage", ft.Container(self.detailsPage, padding=0, expand=True), "startPage")

	def did_mount(self):
		super().did_mount()
		self.page.urt_running = False

	async def update_results_time(self, listview):
		self.page.urt_running = True
		while self.ct == "detailsPage":

			try: #use this here to stop an error appearing when this gets canceled wehen the apps is closed by the user
				await asyncio.sleep(10)
			except: pass

			for index, e in enumerate(listview.controls):
				if listview.page is None: break
				if hasattr(e, "timeText"):
					timedelta = datetime.fromtimestamp(e.timeText.raw_data) - datetime.now()
					timedeltaValue = round(timedelta.total_seconds() / 60)
					if timedeltaValue >= 0:
						e.timeText.value = str(timedeltaValue) + _(" min.")
					else:
						listview.controls.remove(listview.controls[index + 1])
						listview.controls.remove(listview.controls[index])
				listview.page.update()

			if listview.page is not None:
				listview.update()
				if not self.page.urt_running: break


	def display_result_page(self):
		curSe = self.curSe
		listview = ft.ListView(padding=10)
		listview.expand = True
		self.detailsPage.controls.clear()

		self.detailsPage.controls.append(ft.Container(
			ft.Row([ft.Text(curSe["position"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM)],
				   alignment=ft.MainAxisAlignment.CENTER),
			bgcolor=ft.Colors.OUTLINE_VARIANT, padding=10))

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
				"https://www.mvg.de/api/bgw-pt/v3/departures?limit=" + str(resultLimit) + "&offsetInMinutes=0&globalId=" +
				curSe[
					"positionID"])
			departures = json.loads(response.read())
		except:
			self.switch_sub("startPage")
			snBar = ft.SnackBar(ft.Text(_("Error retrieving data.")))
			curSe["page"].overlay.append(snBar)
			snBar.open = True
			self.page.update()
		else:
			if len(departures) < 1:
				self.switch_sub("startPage")
				snBar = ft.SnackBar(ft.Text(_("No departures found.")))
				self.page.overlay.append(snBar)
				snBar.open = True
				self.page.update()
				return

			for d in departures:
				timedelta = datetime.fromtimestamp(d["realtimeDepartureTime"] / 1000) - datetime.now()
				timedeltaValue = round(timedelta.total_seconds() / 60)
				if timedeltaValue < 0: continue

				if "delayInMinutes" in d:
					delayTime = d["delayInMinutes"]
				else:
					delayTime = 0

				lineColor = color_allocator(d["label"])
				if d["label"].startswith("S"):
					cont = ft.Container(ft.Text(d["label"], color=ft.Colors.WHITE), bgcolor=lineColor, width=35,
										alignment=ft.alignment.center, border_radius=10)
				else:
					cont = ft.Container(ft.Text(d["label"], color=ft.Colors.WHITE), bgcolor=lineColor, width=35,
										alignment=ft.alignment.center)

				timeText = ft.Text(str(timedeltaValue) + _(" min."), width=55)
				timeText.raw_data = d["realtimeDepartureTime"] / 1000

				if delayTime > 0:
					timeText.color = ft.Colors.RED

				entry = ft.Row([
					ft.Row([
						cont,
						ft.Text(d["destination"])
					]),
					ft.Row([
						stop_pos_finder(d, curSe),
						timeText,
					], spacing=15)
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				entry.timeText = timeText

				listview.controls.append(entry)
				listview.controls.append(ft.Divider())

		self.switch_sub("detailsPage")
		self.page.run_task(self.update_results_time, listview)
		self.update()

	def switched(self):
		# Reset the loading button when returning to startPage
		if self.goButton.page is not None:
			self.goButton.content = ft.Text(_("Search departures"))
			self.goButton.update()