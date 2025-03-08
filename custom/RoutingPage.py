#!/usr/bin/env python3
# Import flet and systems libraries
import asyncio
import copy
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen

import flet as ft

# Import other parts of this app
from locales import _
from custom import StationSearchBar
from common import MyPage, color_allocator, stop_pos_finder


class RoutingPage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__(_("Connections"), curSe)
		self.curSe = curSe
		curSe["jsonData"] = None
		curSe["time"] = ""

		# Page structure of startRoutingPage
		startRoutingPage = ft.Column()
		self.add_sub("startRoutingPage", ft.Container(startRoutingPage, padding=10))

		fromSearchBar = StationSearchBar.StationSearchBar(hint=_("From"), stations=curSe["stops"])
		startRoutingPage.controls.append(ft.Container(fromSearchBar, alignment=ft.alignment.center))

		toSearchBar = StationSearchBar.StationSearchBar(hint=_("To"), stations=curSe["stops"])
		startRoutingPage.controls.append(ft.Container(toSearchBar, alignment=ft.alignment.center))

		moreRow = ft.Row(vertical_alignment=ft.alignment.center)
		startRoutingPage.controls.append(moreRow)
		timeButtonText = ft.Text(_("Now"), weight=ft.FontWeight.BOLD)
		timeButton = ft.TextButton(
			content=ft.Row([ft.Icon(ft.Icons.ACCESS_TIME), timeButtonText], alignment=ft.MainAxisAlignment.CENTER),
			expand=True)
		moreRow.controls.append(timeButton)
		switchButton = ft.TextButton(icon=ft.Icons.SWAP_VERT, expand=True)
		moreRow.controls.append(switchButton)

		goButton = ft.FilledButton(text=_("Search connections"), expand=True, style=ft.ButtonStyle(color="white"))
		self.goButton = goButton
		startRoutingPage.controls.append(ft.Row(controls=[goButton]))

		startRoutingPage.controls.append(ft.Row())
		historyHeader = ft.Text(_("History"), weight=ft.FontWeight.BOLD)
		startRoutingPage.controls.append(ft.Row(controls=[historyHeader]))

		historyElms = list()

		def toggle_star_button(e):
			e.control.selected = not e.control.selected
			e.control.update()
			e.control.d["star"] = e.control.selected
			curSe["settings"].set_key("connection_history", json.dumps(historyElms, ensure_ascii=False))

		def history_clicked(fromSta, toSta):
			fromSearchBar.value = fromSta
			toSearchBar.value = toSta
			fromSearchBar.update()
			toSearchBar.update()

		historyListView = ft.ListView(controls=[], divider_thickness=1, spacing=5, expand=True)
		startRoutingPage.controls.append(historyListView)

		if curSe["page"].platform is not ft.PagePlatform.ANDROID and curSe["page"].platform is not ft.PagePlatform.IOS:
			historyListView.padding = ft.padding.only(left=10, right=10)

		def process_history():
			nonlocal historyElms
			if curSe["settings"].connection_history != "":
				historyElms = json.loads(curSe["settings"].connection_history)
				historyElms = sorted(historyElms, key=lambda se: (-se["star"], -se["latest"]))
				while len(historyElms) >= 7:
					historyElms.pop()
				curSe["settings"].set_key("connection_history", json.dumps(historyElms, ensure_ascii=False))
				historyListView.controls = []
				for e in historyElms:
					container1 = ft.Text(e["from"])
					container2 = ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.ON_SECONDARY_CONTAINER, size=18)
					container3 = ft.Text(e["to"])
					container4 = ft.Container(expand=True)
					container5 = ft.IconButton(selected=e["star"], icon=ft.Icons.STAR_BORDER,
					                           selected_icon=ft.Icons.STAR, on_click=toggle_star_button)
					container5.d = e
					containerRow = ft.Row(controls=[container1, container2, container3, container4, container5])
					historyListView.controls.append(ft.GestureDetector(containerRow, mouse_cursor=ft.MouseCursor.CLICK,
					                                                   on_tap=(lambda _d, f=e: (
						                                                   history_clicked(f["from"], f["to"])))))

		process_history()

		# listPage (basics more see display_list_page)
		self.listPage = ft.Column()
		self.add_sub("listPage", ft.Container(self.listPage, padding=0, expand=True), "startRoutingPage")

		# resultPage (basics more see display_result_page)
		self.resultPage = ft.Column()
		self.add_sub("resultPage", ft.Container(self.resultPage, padding=0, expand=True), "listPage")

		# functions etc
		def switch_destinations(_e):
			tmpValue = fromSearchBar.value
			fromSearchBar.value = toSearchBar.value
			toSearchBar.value = tmpValue
			curSe["page"].update()

		def choose_time_ok(value, tomorrowCheckboxValue, timeDialog):
			if tomorrowCheckboxValue and value is None:
				value = datetime.now()

			if value is not None and value.strftime("%H:%M") != datetime.now().strftime(
					"%H:%M") or tomorrowCheckboxValue:
				if tomorrowCheckboxValue:
					timeButtonText.value = value.strftime("%H:%M ☼")
					value = value + timedelta(days=1)
					curSe["time"] = value.astimezone(timezone.utc).strftime("&routingDateTime=%Y-%m-%dT%H:%M:00.000Z")
				else:
					timeButtonText.value = value.strftime("%H:%M")
					curSe["time"] = value.astimezone(timezone.utc).strftime("&routingDateTime=%Y-%m-%dT%H:%M:00.000Z")
			else:
				timeButtonText.value = "Jetzt"
				curSe["time"] = ""

			curSe["page"].update()
			curSe["page"].close(timeDialog)

		def choose_time(_e):
			timePicker = ft.CupertinoDatePicker(date_picker_mode=ft.CupertinoDatePickerMode.TIME, use_24h_format=True)
			tomorrowCheckbox = ft.Checkbox(label="Morgen", value=False)
			timeDialog = ft.AlertDialog(title=ft.Text(_("Choose departure time")),
			                            content=ft.Column([ft.Container(timePicker, height=100), tomorrowCheckbox],
			                                              height=130), actions=[
					ft.TextButton(_("Cancel"), on_click=lambda d: curSe["page"].close(timeDialog)),
					ft.TextButton(_("Confirm"),
					              on_click=lambda d: choose_time_ok(timePicker.value, tomorrowCheckbox.value,
					                                                timeDialog))
				])
			curSe["page"].open(timeDialog)

		def do_action(_e):
			curSe["position"] = fromSearchBar.value
			curSe["position2"] = toSearchBar.value
			curSe["positionID"] = None
			curSe["position2ID"] = None

			for s in curSe["stops"]:
				if s["name"] == curSe["position"]:
					curSe["positionID"] = s["id"]
				if s["name"] == curSe["position2"]:
					curSe["position2ID"] = s["id"]
				if (curSe["positionID"] is not None) and (curSe["position2ID"] is not None): break

			if (curSe["positionID"] is not None) and (curSe["position2ID"] is not None):
				goButton.content = ft.ProgressRing(width=14, height=14, color=ft.Colors.ON_PRIMARY, stroke_width=2)
				goButton.update()

				# add to history
				found = False
				for e in historyElms:
					if e["from"] == fromSearchBar.value and e["to"] == toSearchBar.value:
						found = True
						e["latest"] = time.time()
				if not found:
					d = {"from": fromSearchBar.value, "to": toSearchBar.value, "latest": time.time(), "star": False}
					historyElms.append(d)
				curSe["settings"].set_key("connection_history", json.dumps(historyElms, ensure_ascii=False))
				process_history()

				# load list page
				self.curSe["jsonData"] = None
				self.display_list_page()
			else:
				snBar = ft.SnackBar(ft.Text(_("Unknown stop")))
				curSe["page"].overlay.append(snBar)
				snBar.open = True
				curSe["page"].update()

		timeButton.on_click = choose_time
		switchButton.on_click = switch_destinations
		goButton.on_click = do_action

	def did_mount(self):
		super().did_mount()
		self.page.udt_running = False

	async def update_results_time(self, listview):
		self.page.udt_running = True
		while self.ct == "listPage" or self.ct == "resultPage":

			try:  # use this here to stop an error appearing when this gets canceled wehen the apps is closed by the user
				await asyncio.sleep(10)
			except:
				pass

			for index, e in enumerate(listview.controls):
				if listview.page is None: break
				if hasattr(e, "timeText"):
					timedeltaValue = round((e.timeText.raw_data - datetime.now()).total_seconds() / 60)
					if timedeltaValue >= 0:
						e.timeText.value = _("in ") + str(timedeltaValue) + _(" min.")
					else:
						timedeltaValue = timedeltaValue * -1
						e.timeText.value = _("before ") + str(timedeltaValue) + _(" min.")

			if listview.page is not None:
				listview.update()
				if not self.page.udt_running: break

	def display_list_page(self):
		curSe = self.curSe
		listContainer = ft.Column(expand=True, spacing=0)
		listContainer.expand = True
		self.listPage.controls.clear()
		self.listPage.controls.append(listContainer)
		self.listPage.expand = True

		sInfo = [
			ft.Text(curSe["position"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
			ft.Icon(name=ft.Icons.ARROW_FORWARD),
			ft.Text(curSe["position2"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
		]
		listContainer.controls.append(ft.Container(ft.Row(controls=sInfo, alignment=ft.MainAxisAlignment.CENTER),
		                                           bgcolor=ft.Colors.OUTLINE_VARIANT, padding=10))

		listview = ft.ListView(padding=10, expand=True)
		listview.padding = ft.padding.only(top=2)
		listContainer.controls.append(listview)

		def animate(_d, rid, tid):
			curSe["jsonData"] = rid
			curSe["duration"] = tid
			self.display_result_page()
			self.switch_sub("resultPage")

		if curSe["settings"].results == 0:
			resultLimit = 7
		elif curSe["settings"].results == 1:
			resultLimit = 12
		else:
			resultLimit = 17

		try:
			if curSe["jsonData"] is None:
				response = urlopen(
					"https://www.mvg.de/api/bgw-pt/v3/routes?transportTypes=SCHIFF,RUFTAXI,BAHN,UBAHN,TRAM,SBAHN,BUS,REGIONAL_BUS&numberOfConnections=" + str(
					resultLimit) + "&originStationGlobalId=" + curSe["positionID"] + "&destinationStationGlobalId=" +
				                   curSe["position2ID"] + curSe["time"])
				routes = json.loads(response.read())
				curSe["routes"] = routes
			else:
				routes = curSe["routes"]
		except Exception as e:
			print(e)
			self.switch_sub("startRoutingPage")
			snBar = ft.SnackBar(ft.Text(_("Error retrieving data.")))
			curSe["page"].overlay.append(snBar)
			snBar.open = True
			curSe["page"].update()
		else:
			if len(routes) < 1:
				self.switch_sub("startRoutingPage")
				snBar = ft.SnackBar(ft.Text(_("No connections found.")))
				self.page.overlay.append(snBar)
				snBar.open = True
				self.page.update()
				return

			for r in routes:
				rp = dict()
				rp["starttime"] = datetime.strptime(r["parts"][0]["from"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
				if "departureDelayInMinutes" in r["parts"][0]["from"]:
					rp["starttimeDelay"] = r["parts"][0]["from"]["departureDelayInMinutes"]
					rp["starttime"] = rp["starttime"] + timedelta(minutes=rp["starttimeDelay"])
				else:
					rp["starttimeDelay"] = 0
				rp["endtime"] = datetime.strptime(r["parts"][-1]["to"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
				if "arrivalDelayInMinutes" in r["parts"][-1]["to"]:
					rp["endtimeDelay"] = r["parts"][-1]["to"]["arrivalDelayInMinutes"]
					rp["endtime"] = rp["endtime"] + timedelta(minutes=rp["endtimeDelay"])
				else:
					rp["endtimeDelay"] = 0  # var curently not used
				rp["id"] = r["uniqueId"]
				rp["timedeltaValue"] = round((rp["starttime"] - datetime.now()).total_seconds() / 60)
				rp["traveltimedeltaValue"] = round((rp["endtime"] - rp["starttime"]).total_seconds() / 60) + rp[
					"starttimeDelay"]

				if rp["timedeltaValue"] < 0: continue

				partLables = ft.Row(spacing=5)
				for p in r["parts"]:
					label = p["line"]["label"]

					if label == "" or p["line"]["sev"] == True:
						label = "SEV"  # todo: show line number of sev if it exists (needs changes in color_allocator)

					if label == "Fussweg":
						cont = ft.Container(ft.Icon(ft.Icons.DIRECTIONS_WALK, color=ft.Colors.INVERSE_SURFACE, size=15),
						                    width=35)
						partLables.controls.append(cont)
					elif label == "SEV":
						cont = ft.Container(ft.Text(label[:4], color=ft.Colors.WHITE, no_wrap=True),
						                    bgcolor="transparent",
						                    width=35, alignment=ft.alignment.center,
						                    image=ft.DecorationImage(src="sev_hexagon.png", fit=ft.ImageFit.FILL))
						partLables.controls.append(cont)
					elif label.startswith("S"):
						if label.startswith("S8"):
							c = "#f2c531"
						else:
							c = ft.Colors.WHITE

						cont = ft.Container(ft.Text(label[:4], color=c, no_wrap=True), bgcolor=color_allocator(label),
						                    width=35, alignment=ft.alignment.center, border_radius=10)
						partLables.controls.append(cont)
					else:
						cont = ft.Container(ft.Text(label[:4], color=ft.Colors.WHITE, no_wrap=True),
						                    bgcolor=color_allocator(label),
						                    width=35, alignment=ft.alignment.center)
						partLables.controls.append(cont)

				timeText = ft.Text("in " + str(rp["timedeltaValue"]) + _(" min."), weight=ft.FontWeight.BOLD,
				                   color=ft.Colors.PRIMARY)
				if rp["starttimeDelay"] > 2:
					timeText.color = ft.Colors.RED
				timeText.raw_data = rp["starttime"]
				entry = ft.Row([
					ft.Row([
						ft.Column([ft.Text(" " + rp["starttime"].strftime("%H:%M")),
						           ft.Text(rp["endtime"].strftime("%H:%M"), size=12)], spacing=2,
						          horizontal_alignment=ft.CrossAxisAlignment.END),
						partLables
					], spacing=15),
					ft.Row([
						ft.Column([timeText,
						           ft.Text(_("Duration: ") + str(rp["traveltimedeltaValue"]) + _(" min."), size=12)],
						          spacing=2,
						          horizontal_alignment=ft.CrossAxisAlignment.END),
						ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=ft.Colors.INVERSE_SURFACE, size=18)
					], spacing=5),
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				entryContainer = ft.Container(content=entry,
				                              padding=ft.padding.only(left=10, right=10, top=7, bottom=7), ink=True,
				                              on_click=lambda f, d=r, t=str(rp["traveltimedeltaValue"]),: animate(f, d,
				                                                                                                  t))
				entryContainer.timeText = timeText

				listview.controls.append(entryContainer)
				listview.controls.append(ft.Divider(thickness=1, height=1))

		self.switch_sub("listPage")
		self.page.run_task(self.update_results_time, listview)

	def display_result_page(self):
		curSe = self.curSe
		listContainer = ft.Column(expand=True, spacing=0)
		listContainer.expand = True
		self.resultPage.controls.clear()
		self.resultPage.controls.append(listContainer)
		self.resultPage.expand = True

		sInfo = [
			ft.Text(curSe["position"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
			ft.Icon(name=ft.Icons.ARROW_FORWARD),
			ft.Text(curSe["position2"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
		]
		listContainer.controls.append(ft.Container(ft.Row(controls=sInfo, alignment=ft.MainAxisAlignment.CENTER),
		                                           bgcolor=ft.Colors.OUTLINE_VARIANT, padding=10))
		mColumn = ft.Column(expand=True)
		listContainer.controls.append(mColumn)
		mStack = ft.Stack(expand=True)
		mColumn.controls.append(mStack)
		listview = ft.ListView(expand=True, spacing=0)
		mStack.controls.append(listview)

		ePL = ft.ExpansionPanelList(expand=True, elevation=0, expand_icon_color=ft.Colors.PRIMARY,
		                            expanded_header_padding=ft.padding.symmetric(vertical=8.0))
		listview.controls.append(ePL)

		spaceAfterTime = 45

		rid = curSe["jsonData"]
		for index, p in enumerate(rid["parts"]):
			pData = dict()
			pData["fromStation"] = p["from"]["name"]
			pData["fromTime"] = datetime.strptime(p["from"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
			pData["line"] = p["line"]["label"]
			if pData["line"] == "" or p["line"]["sev"] == True:
				pData["line"] = "SEV"
			pData["lineDestination"] = p["line"]["destination"]
			pData["toStation"] = p["to"]["name"]
			pData["toTime"] = datetime.strptime(p["to"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")

			if "departureDelayInMinutes" in p["from"]:
				pData["fromTimeDelay"] = p["from"]["departureDelayInMinutes"]
			else:
				pData["fromTimeDelay"] = 0

			if "arrivalDelayInMinutes" in p["to"]:
				pData["toTimeDelay"] = p["to"]["arrivalDelayInMinutes"]
			else:
				pData["toTimeDelay"] = 0

			if pData["fromTimeDelay"] > 0:
				delayHint = " (+" + str(pData["fromTimeDelay"]) + ")"
				spaceAfterTime = 70
			else:
				delayHint = ""

			if pData["toTimeDelay"] > 0:
				delayHintTo = " (+" + str(pData["toTimeDelay"]) + ")"
				spaceAfterTime = 70
			else:
				delayHintTo = ""

			if index != len(rid["parts"]) - 1 and "departureDelayInMinutes" in rid["parts"][index + 1]["from"] and \
					rid["parts"][index + 1]["from"]["departureDelayInMinutes"] > 0:
				delayHintNext = " (+" + str(rid["parts"][index + 1]["from"]["departureDelayInMinutes"]) + ")"
				spaceAfterTime = 70
			else:
				delayHintNext = "     "

			if curSe["settings"].messages_show == "current":
				# remove non disruption-type messages if choosen so in settings (default)
				if pData["line"] in self.curSe["rps"]:
					msg = self.curSe["rps"][pData["line"]]
					msg.expanded = False
					msgCopy = copy.deepcopy(msg)

					newC = [elm for elm in msgCopy.content.content.controls if hasattr(elm, "myIsCurrent")]
					msgCopy.content.content.controls = newC
					msgCopy.content.content.controls.append(ft.Container(expand=True))

					ePL.controls.insert(1, msgCopy)
			else:
				if pData["line"] in self.curSe["rps_all"]:
					msg = self.curSe["rps_all"][pData["line"]]
					msg.expanded = False
					msgCopy = copy.deepcopy(msg)
					msgCopy.content.content.controls.append(ft.Container(expand=True))
					ePL.controls.insert(1, msgCopy)

			if index == 0:
				fromStationBorder = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
				                                   top=ft.border.BorderSide(4, color_allocator(pData["line"])))
				fromStationRow = ft.Row([
					ft.Row([
						ft.Text(pData["fromTime"].strftime("%H:%M") + delayHint, width=spaceAfterTime),
						ft.Container(width=10, height=25, border=fromStationBorder, padding=ft.padding.all(0),
						             margin=ft.margin.only(top=20)),
						ft.Text(pData["fromStation"], size=15)
					], spacing=15),
					stop_pos_finder(p["from"], curSe),
					# ft.Row([ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=ft.Colors.INVERSE_SURFACE, size=18)], spacing=5), todo make this button work
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				listview.controls.append(ft.Container(fromStationRow, padding=ft.padding.symmetric(horizontal=10)))

			betweenStopsList = []
			for stop in p["intermediateStops"]:
				if "departureDelayInMinutes" in stop and stop["departureDelayInMinutes"] > 0:
					delayHint = " (+" + str(stop["departureDelayInMinutes"]) + ")"
				else:
					delayHint = "     "
				betweenStopTime = datetime.strptime(stop["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
				infoText = ft.Text(betweenStopTime.strftime("%H:%M") + delayHint + "     " + stop["name"], size=12)
				betweenStopsList.append(infoText)

			if len(betweenStopsList) < 1:
				betweenStopsList.append(ft.Text(_("No stops in between."), size=12))

			betweenStopsList.append(ft.Text(" ", size=1))

			if pData["line"] == "Fussweg":
				kmLabel = ft.Text(str(int(p["distance"])) + _(" Meter"))
				betweenStationLabel = ft.Row([ft.Container(
					ft.Icon(ft.Icons.DIRECTIONS_WALK, color=ft.Colors.INVERSE_SURFACE, size=15), width=35), kmLabel])
			elif pData["line"] == "SEV":
				betweenStationLabel = ft.Container(
					ft.Text(pData["line"][:4], color=ft.Colors.WHITE, size=14, no_wrap=True),
					bgcolor="transparent", width=35,
					alignment=ft.alignment.center,
					image=ft.DecorationImage(src="sev_hexagon.png", fit=ft.ImageFit.FILL))
			elif pData["line"].startswith("S"):
				if pData["line"].startswith("S8"):
					c = "#f2c531"
				else:
					c = ft.Colors.WHITE

				betweenStationLabel = ft.Container(
					ft.Text(pData["line"][:4], color=c, size=14, no_wrap=True),
					bgcolor=color_allocator(pData["line"]), width=35,
					alignment=ft.alignment.center, border_radius=10)
			else:
				betweenStationLabel = ft.Container(
					ft.Text(pData["line"][:4], color=ft.Colors.WHITE, size=14, no_wrap=True),
				                                   bgcolor=color_allocator(pData["line"]), width=35,
				                                   alignment=ft.alignment.center)

			betweenStationTile = ft.ExpansionTile(
				title=ft.Row([betweenStationLabel, ft.Text(pData["lineDestination"], size=14)]),
				affinity=ft.TileAffinity.TRAILING,
				controls=[ft.Column(controls=betweenStopsList)],
				expand=True,
				collapsed_icon_color=ft.Colors.with_opacity(0.0, ft.Colors.PRIMARY)
			)
			betweenStationRow = ft.Row([
				ft.Text("", width=spaceAfterTime),
				ft.Container(betweenStationTile, expand=True,
				             border=ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"]))))
			], spacing=15, expand=True)
			listview.controls.append(ft.Container(betweenStationRow, padding=ft.padding.symmetric(horizontal=10)))

			if index != len(rid["parts"]) - 1:
				toStationBorderTop = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
				                                    bottom=ft.border.BorderSide(4, color_allocator(pData["line"])))
				nextLine = rid["parts"][index + 1]["line"]["label"]
				if nextLine == "" or rid["parts"][index + 1]["line"]["sev"] == True:
					nextLine = "SEV"
				toStationBorderBottom = ft.border.only(
					left=ft.border.BorderSide(4, color_allocator(nextLine)),
					top=ft.border.BorderSide(4, color_allocator(nextLine)))
				nextStationTime = datetime.strptime(rid["parts"][index + 1]["from"]["plannedDeparture"][:-6],
				                                    "%Y-%m-%dT%H:%M:%S")

				toStationRow = ft.Row([
					ft.Row([
						ft.Column([
							ft.Text(pData["toTime"].strftime("%H:%M") + delayHint, width=spaceAfterTime),
							ft.Text(nextStationTime.strftime("%H:%M") + delayHintNext, width=spaceAfterTime)
						], spacing=0),
						ft.Column([
							ft.Container(width=10, height=25, border=toStationBorderTop, padding=ft.padding.all(0)),
							ft.Container(width=10, height=25, border=toStationBorderBottom, padding=ft.padding.all(0))
						]),
						ft.Text(pData["toStation"], size=15),
					], spacing=15),
					ft.Column(
						[stop_pos_finder(p["to"], curSe), stop_pos_finder(rid["parts"][index + 1]["from"], curSe)]),
					# ft.Row([ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=ft.Colors.INVERSE_SURFACE, size=18)], spacing=5), todo make this button work
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				listview.controls.append(ft.Container(toStationRow, padding=ft.padding.symmetric(horizontal=10)))
			else:
				toStationBorder = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
				                                 bottom=ft.border.BorderSide(4, color_allocator(pData["line"])))
				toStationRow = ft.Row([
					ft.Row([
						ft.Text(pData["toTime"].strftime("%H:%M") + delayHintTo, width=spaceAfterTime),
						ft.Container(width=10, height=25, border=toStationBorder, padding=ft.padding.all(0),
						             margin=ft.margin.only(bottom=20)),
						ft.Text(pData["toStation"], size=15)
					], spacing=15),
					stop_pos_finder(p["to"], curSe),
					# ft.Row([ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=ft.Colors.INVERSE_SURFACE, size=18)], spacing=5),  todo make this button work
				], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
				listview.controls.append(ft.Container(toStationRow, padding=ft.padding.symmetric(horizontal=10)))

		listview.controls.append(ft.Divider(thickness=1))
		listview.controls.append(
			ft.Text(_("Duration: ") + curSe["duration"] + _(" min."), size=12, expand=True,
			        text_align=ft.TextAlign.CENTER))
		self.update()

	def switched(self):
		# Reset the loading button when returning to startPage
		if self.goButton.page is not None:
			self.goButton.content = ft.Text(_("Search connections"))
			self.goButton.update()
