#!/usr/bin/env python3
# Import flet and systems libraries
import json
from datetime import datetime
from urllib.request import urlopen

import flet as ft

# Import other parts of this app
from pages import StationSearchBar
from common import MyPage, color_allocator, stop_pos_finder


class RoutingPage(MyPage):
    def __init__(self, curSe):
        # basics
        super().__init__("Verbindungen", curSe)
        self.curSe = curSe
        curSe["jsonData"] = None
        curSe["time"] = ""

        # Page structure of startRoutingPage
        startRoutingPage = ft.Column()
        self.add_sub("startRoutingPage", ft.Container(startRoutingPage, padding=10))

        fromSearchBar = StationSearchBar.StationSearchBar(hint="Von", stations=curSe["stops"])
        startRoutingPage.controls.append(ft.Container(fromSearchBar, alignment=ft.alignment.center))

        toSearchBar = StationSearchBar.StationSearchBar(hint="Nach", stations=curSe["stops"])
        startRoutingPage.controls.append(ft.Container(toSearchBar, alignment=ft.alignment.center))

        moreRow = ft.Row(vertical_alignment=ft.alignment.center)
        startRoutingPage.controls.append(moreRow)
        timeButtonText = ft.Text("Jetzt", weight=ft.FontWeight.BOLD)
        timeButton = ft.TextButton(
            content=ft.Row([ft.Icon(ft.icons.ACCESS_TIME), timeButtonText], alignment=ft.MainAxisAlignment.CENTER),
            expand=True)
        moreRow.controls.append(timeButton)
        switchButton = ft.TextButton(icon=ft.icons.SWAP_VERT, expand=True)
        moreRow.controls.append(switchButton)

        goButton = ft.FilledButton(text="Verbindungen anzeigen", expand=True, style=ft.ButtonStyle(color="white"))
        self.goButton = goButton
        startRoutingPage.controls.append(ft.Row(controls=[goButton]))

        startRoutingPage.controls.append(ft.Row())
        historyHeader = ft.Text("Verlauf", weight=ft.FontWeight.BOLD)
        startRoutingPage.controls.append(ft.Row(controls=[historyHeader]))

        container2 = ft.Container(expand=True)
        container2.content = ft.Text("Non clickable")

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

        def choose_time_ok(value, timeDialog):
            if value is not None and value.strftime("%H:%M") != datetime.now().strftime("%H:%M"):
                timeButtonText.value = value.strftime("%H:%M")
                curSe["time"] = value.strftime("&routingDateTime=%Y-%m-%dT%H:%M:00.000Z")
            else:
                timeButtonText.value = "Jetzt"
                curSe["time"] = ""

            curSe["page"].update()
            curSe["page"].close(timeDialog)

        def choose_time(_e):
            timePicker = ft.CupertinoDatePicker(date_picker_mode=ft.CupertinoDatePickerMode.TIME, use_24h_format=True)
            timeDialog = ft.AlertDialog(title=ft.Text("Abfahrtszeit wählen"),
                                        content=ft.Container(timePicker, height=150), actions=[
                    ft.TextButton("Abbrechen", on_click=lambda d: curSe["page"].close(timeDialog)),
                    ft.TextButton("Bestätigen", on_click=lambda d: choose_time_ok(timePicker.value, timeDialog))
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
                goButton.content = ft.ProgressRing(width=14, height=14, color=ft.colors.ON_PRIMARY, stroke_width=2)
                goButton.update()
                self.curSe["jsonData"] = None
                self.display_list_page()
            else:
                curSe["page"].snack_bar = ft.SnackBar(ft.Text(f"Unbekannte Haltestelle"))
                curSe["page"].snack_bar.open = True
                curSe["page"].update()

        timeButton.on_click = choose_time
        switchButton.on_click = switch_destinations
        goButton.on_click = do_action

    def display_list_page(self):
        curSe = self.curSe
        listContainer = ft.Column(expand=True, spacing=0)
        listContainer.expand = True
        self.listPage.controls.clear()
        self.listPage.controls.append(listContainer)
        self.listPage.expand = True

        sInfo = [
            ft.Text(curSe["position"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            ft.Icon(name=ft.icons.ARROW_FORWARD),
            ft.Text(curSe["position2"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
        ]
        listContainer.controls.append(ft.Container(ft.Row(controls=sInfo, alignment=ft.MainAxisAlignment.CENTER),
                                                   bgcolor=ft.colors.OUTLINE_VARIANT, padding=10))

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
                response = urlopen("https://www.mvg.de/api/fib/v2/connection?numberOfConnections=" + str(
                    resultLimit) + "&originStationGlobalId=" + curSe["positionID"] + "&destinationStationGlobalId=" +
                                   curSe["position2ID"] + curSe["time"])
                routes = json.loads(response.read())
                curSe["routes"] = routes
            else:
                routes = curSe["routes"]
        except Exception as e:
            print(e)
            self.switch_sub("startRoutingPage")
            curSe["page"].snack_bar = ft.SnackBar(ft.Text(f"Fehler beim Datenabruf"))
            curSe["page"].snack_bar.open = True
            curSe["page"].update()
        else:
            if len(routes) < 1:
                self.switch_sub("startRoutingPage")
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Keine Verbindungen gefunden"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            for r in routes:
                rp = dict()
                rp["starttime"] = datetime.strptime(r["parts"][0]["from"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
                rp["endtime"] = datetime.strptime(r["parts"][-1]["to"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
                rp["id"] = r["uniqueId"]
                rp["timedeltaValue"] = round((rp["starttime"] - datetime.now()).total_seconds() / 60)
                rp["traveltimedeltaValue"] = round((rp["endtime"] - rp["starttime"]).total_seconds() / 60)

                if rp["timedeltaValue"] < 0: continue

                partLables = ft.Row(spacing=5)
                for p in r["parts"]:
                    label = p["line"]["label"]
                    if label == "Fussweg":
                        cont = ft.Container(ft.Icon(ft.icons.DIRECTIONS_WALK, color=ft.colors.INVERSE_SURFACE, size=15),
                                            width=35)
                        partLables.controls.append(cont)
                    elif label.startswith("S"):
                        cont = ft.Container(ft.Text(label, color=ft.colors.WHITE), bgcolor=color_allocator(label),
                                            width=35, alignment=ft.alignment.center, border_radius=10)
                        partLables.controls.append(cont)
                    else:
                        cont = ft.Container(ft.Text(label, color=ft.colors.WHITE), bgcolor=color_allocator(label),
                                            width=35, alignment=ft.alignment.center)
                        partLables.controls.append(cont)

                entry = ft.Row([
                    ft.Row([
                        ft.Column([ft.Text(" " + rp["starttime"].strftime("%H:%M")),
                                   ft.Text(rp["endtime"].strftime("%H:%M"), size=12)], spacing=2,
                                  horizontal_alignment=ft.CrossAxisAlignment.END),
                        partLables
                    ], spacing=15),
                    ft.Row([
                        ft.Column([ft.Text("in " + str(rp["timedeltaValue"]) + " Min.", weight=ft.FontWeight.BOLD,
                                           color=ft.colors.PRIMARY),
                                   ft.Text("Dauer: " + str(rp["traveltimedeltaValue"]) + " Min.", size=12)], spacing=2,
                                  horizontal_alignment=ft.CrossAxisAlignment.END),
                        ft.Icon(ft.icons.ARROW_FORWARD_IOS, color=ft.colors.INVERSE_SURFACE, size=18)
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                entryContainer = ft.Container(content=entry,
                                              padding=ft.padding.only(left=10, right=10, top=7, bottom=7), ink=True,
                                              on_click=lambda f, d=r, t=str(rp["traveltimedeltaValue"]),: animate(f, d,
                                                                                                                  t))
                listview.controls.append(entryContainer)
                listview.controls.append(ft.Divider(thickness=1, height=1))

        self.switch_sub("listPage")

    def display_result_page(self):
        curSe = self.curSe
        listContainer = ft.Column(expand=True, spacing=0)
        listContainer.expand = True
        self.resultPage.controls.clear()
        self.resultPage.controls.append(listContainer)
        self.resultPage.expand = True

        sInfo = [
            ft.Text(curSe["position"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            ft.Icon(name=ft.icons.ARROW_FORWARD),
            ft.Text(curSe["position2"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM)
        ]
        listContainer.controls.append(ft.Container(ft.Row(controls=sInfo, alignment=ft.MainAxisAlignment.CENTER),
                                                   bgcolor=ft.colors.OUTLINE_VARIANT, padding=10))
        mColumn = ft.Column(expand=True)
        listContainer.controls.append(mColumn)
        mStack = ft.Stack(expand=True)
        mColumn.controls.append(mStack)
        listview = ft.ListView(expand=True, spacing=0)
        mStack.controls.append(listview)

        ePL = ft.ExpansionPanelList(expand=True, elevation=0)
        listview.controls.append(ePL)

        rid = curSe["jsonData"]
        for index, p in enumerate(rid["parts"]):
            pData = dict()
            pData["fromStation"] = p["from"]["name"]
            pData["fromTime"] = datetime.strptime(p["from"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
            pData["line"] = p["line"]["label"]
            pData["lineDestination"] = p["line"]["destination"]
            pData["toStation"] = p["to"]["name"]
            pData["toTime"] = datetime.strptime(p["to"]["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")

            if pData["line"] in self.curSe["rps"]:
                msg = self.curSe["rps"][pData["line"]]
                ePL.controls.insert(1, msg)
                # todo do not show added not "current" info

            if index == 0:
                fromStationBorder = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
                                                   top=ft.border.BorderSide(4, color_allocator(pData["line"])))
                fromStationRow = ft.Row([
                    ft.Row([
                        ft.Text(pData["fromTime"].strftime("%H:%M"), width=45),
                        ft.Container(width=10, height=25, border=fromStationBorder, padding=ft.padding.all(0),
                                     margin=ft.margin.only(top=20)),
                        ft.Text(pData["fromStation"], size=15)
                    ], spacing=15),
                    stop_pos_finder(p["from"], curSe),
                   # ft.Row([ft.Icon(ft.icons.ARROW_FORWARD_IOS, color=ft.colors.INVERSE_SURFACE, size=18)], spacing=5), todo make this button work
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                listview.controls.append(ft.Container(fromStationRow, padding=ft.padding.symmetric(horizontal=10)))

            betweenStopsList = []
            for stop in p["intermediateStops"]:
                betweenStopTime = datetime.strptime(stop["plannedDeparture"][:-6], "%Y-%m-%dT%H:%M:%S")
                infoText = ft.Text(betweenStopTime.strftime("%H:%M") + "     " + stop["name"], size=12)
                betweenStopsList.append(infoText)

            if len(betweenStopsList) < 1:
                betweenStopsList.append(ft.Text("Keine Zwischenhalte.", size=12))

            betweenStopsList.append(ft.Text(" ", size=1))

            if pData["line"] == "Fussweg":
                kmLabel = ft.Text(str(int(p["distance"])) + " Meter")
                betweenStationLabel = ft.Row([ft.Container(
                    ft.Icon(ft.icons.DIRECTIONS_WALK, color=ft.colors.INVERSE_SURFACE, size=15), width=35), kmLabel])
            else:
                betweenStationLabel = ft.Container(ft.Text(pData["line"], color=ft.colors.WHITE, size=14),
                                                   bgcolor=color_allocator(pData["line"]), width=35,
                                                   alignment=ft.alignment.center)

            betweenStationTile = ft.ExpansionTile(
                title=ft.Row([betweenStationLabel, ft.Text(pData["lineDestination"], size=14)]),
                affinity=ft.TileAffinity.TRAILING,
                controls=[ft.Column(controls=betweenStopsList)],
                expand=True,
                collapsed_icon_color=ft.colors.with_opacity(0.0, ft.colors.PRIMARY)
            )
            betweenStationRow = ft.Row([
                ft.Text("", width=45),
                ft.Container(betweenStationTile, expand=True,
                             border=ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"]))))
            ], spacing=15, expand=True)
            listview.controls.append(ft.Container(betweenStationRow, padding=ft.padding.symmetric(horizontal=10)))

            if index != len(rid["parts"]) - 1:
                toStationBorderTop = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
                                                    bottom=ft.border.BorderSide(4, color_allocator(pData["line"])))
                toStationBorderBottom = ft.border.only(
                    left=ft.border.BorderSide(4, color_allocator(rid["parts"][index + 1]["line"]["label"])),
                    top=ft.border.BorderSide(4, color_allocator(rid["parts"][index + 1]["line"]["label"])))
                nextStationTime = datetime.strptime(rid["parts"][index + 1]["from"]["plannedDeparture"][:-6],
                                                    "%Y-%m-%dT%H:%M:%S")
                toStationRow = ft.Row([
                    ft.Row([
                        ft.Column([
                            ft.Text(pData["toTime"].strftime("%H:%M"), width=45),
                            ft.Text(nextStationTime.strftime("%H:%M"), width=45)
                        ], spacing=0),
                        ft.Column([
                            ft.Container(width=10, height=25, border=toStationBorderTop, padding=ft.padding.all(0)),
                            ft.Container(width=10, height=25, border=toStationBorderBottom, padding=ft.padding.all(0))
                        ]),
                        ft.Text(pData["toStation"], size=15),
                    ], spacing=15),
                    ft.Column([stop_pos_finder(p["to"], curSe), stop_pos_finder(rid["parts"][index + 1]["from"], curSe)]),
                    #ft.Row([ft.Icon(ft.icons.ARROW_FORWARD_IOS, color=ft.colors.INVERSE_SURFACE, size=18)], spacing=5), todo make this button work
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                listview.controls.append(ft.Container(toStationRow, padding=ft.padding.symmetric(horizontal=10)))
            else:
                toStationBorder = ft.border.only(left=ft.border.BorderSide(4, color_allocator(pData["line"])),
                                                 bottom=ft.border.BorderSide(4, color_allocator(pData["line"])))
                toStationRow = ft.Row([
                    ft.Row([
                        ft.Text(pData["toTime"].strftime("%H:%M"), width=45),
                        ft.Container(width=10, height=25, border=toStationBorder, padding=ft.padding.all(0),
                                     margin=ft.margin.only(bottom=20)),
                        ft.Text(pData["toStation"], size=15)
                    ], spacing=15),
                    stop_pos_finder(p["to"], curSe),
                    #ft.Row([ft.Icon(ft.icons.ARROW_FORWARD_IOS, color=ft.colors.INVERSE_SURFACE, size=18)], spacing=5),  todo make this button work
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                listview.controls.append(ft.Container(toStationRow, padding=ft.padding.symmetric(horizontal=10)))

        listview.controls.append(ft.Divider(thickness=1))
        listview.controls.append(
            ft.Text("Dauer: " + curSe["duration"] + " Min.", size=12, expand=True, text_align=ft.TextAlign.CENTER))
        self.update()

    def switched(self):
        # Reset the loading button when returning to startPage
        if self.goButton.page is not None:
            self.goButton.content = ft.Text("Verbindungen anzeigen")
            self.goButton.update()
