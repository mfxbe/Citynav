#!/usr/bin/env python3
# Import pyodide_http for API requests to work
import pyodide_http

pyodide_http.patch_all()

# Import flet and systems libraries
import flet as ft
import json

# Import other parts of this app
import stopsdata  # contains also the static data (#FIXME provide static as json text file)
import DeparturePage
import ReportsPage
import MapsPage
import RoutingPage
from common import StorageHandler

curSe = {}


# Load the information about stops
def load_stops():
	stopsResult = []
	stopsData = json.loads(stopsdata.stops)

	for s in stopsData:
		if not any(stop["name"] == s["Name mit Ort"] for stop in stopsResult):
			if s["Tarifzone TSR"] != "":
				stop = dict()
				stop["name"] = s["Name mit Ort"]
				stop["id"] = s["Globale ID"]
				stopsResult.append(stop)

	return stopsResult


# Main function for app startup
def main(page: ft.Page):
	global curSe

	# basic
	page.title = "Citynav München"
	page.window.width = 400

	# set basic common data
	curSe["stops"] = load_stops()  # load stop data
	curSe["page"] = page
	curSe["settings"] = StorageHandler(page)

	# Some color fixes and preferences
	# page.theme_mode = ft.ThemeMode.DARK
	page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary=ft.colors.BACKGROUND),
						  search_bar_theme=ft.SearchBarTheme(elevation=1))
	page.dark_theme = ft.theme.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary="#272a2f"),
									 text_theme=ft.TextTheme(
										 title_medium=ft.TextStyle(weight=ft.FontWeight.NORMAL, color="white")))

	# setup pages
	routingPage = RoutingPage.RoutingPage(curSe)
	departurePage = DeparturePage.DeparturePage(curSe)
	reportsPage = ReportsPage.ReportsPage(curSe)
	mapsPage = MapsPage.MapsPage(curSe)
	mainContainer = ft.Container(content=routingPage)
	page.add(mainContainer)
	mainContainer.expand = True
	page.padding = 0

	# Add mobile navigation bar to page
	def route_changer(e):
		index = e.control.selected_index
		if index == 0:
			nonlocal routingPage
			if mainContainer.content == routingPage:
				routingPage = RoutingPage.RoutingPage(curSe)
			mainContainer.content = routingPage
		elif index == 1:
			nonlocal departurePage
			if mainContainer.content == departurePage:
				departurePage = DeparturePage.DeparturePage(curSe)
			mainContainer.content = departurePage
		elif index == 2:
			nonlocal reportsPage
			if mainContainer.content == reportsPage:
				reportsPage = ReportsPage.ReportsPage(curSe)
			mainContainer.content = reportsPage
		elif index == 3:
			nonlocal mapsPage
			if mainContainer.content == mapsPage:
				mapsPage = MapsPage.MapsPage(curSe)
			mainContainer.content = mapsPage

		mainContainer.update()

	page.navigation_bar = ft.NavigationBar(
		destinations=[ft.NavigationBarDestination(icon=ft.icons.ROUTE, label="Verbindungen"),
					  ft.NavigationBarDestination(icon=ft.icons.NEAR_ME, label="Abfahrten"),
					  ft.NavigationBarDestination(icon=ft.icons.LIST, label="Meldungen"),
					  ft.NavigationBarDestination(icon=ft.icons.MAP, label="Netzpläne")], selected_index=0,
		on_change=route_changer)

	#set theme type
	page.theme_mode = curSe["settings"].theme

	# update page to present
	page.update()


ft.app(main)
