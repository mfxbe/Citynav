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
	stop_names = set()

	for s in stopsData:
		stop_name = s["Name mit Ort"]
		if stop_name not in stop_names:  # Überprüfen, ob der Stopname bereits vorhanden ist
			if s["Tarifzone TSR"] != "":
				stop = {
					"name": stop_name,
					"id": s["Globale ID"]
				}
				stopsResult.append(stop)
				stop_names.add(stop_name)  # Stopname zum Set hinzufügen

	return stopsResult


# Main function for app startup
def main(page: ft.Page):
	global curSe

	# basic
	page.title = "Citynav München"

	# set basic common data
	curSe["stops"] = load_stops()  # load stop data
	curSe["page"] = page
	curSe["settings"] = StorageHandler(page)

	# Some color fixes and preferences
	# page.theme_mode = ft.ThemeMode.DARK
	page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary=ft.colors.BACKGROUND),
						  search_bar_theme=ft.SearchBarTheme(elevation=1),
						  system_overlay_style=ft.SystemOverlayStyle(status_bar_brightness=ft.Brightness.DARK))
	page.dark_theme = ft.theme.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary="#272a2f"),
									 text_theme=ft.TextTheme(
										 title_medium=ft.TextStyle(weight=ft.FontWeight.NORMAL, color="white")),
									 system_overlay_style=ft.SystemOverlayStyle(
										 status_bar_brightness=ft.Brightness.DARK))

	# setup pages
	routingPage = RoutingPage.RoutingPage(curSe)
	departurePage = DeparturePage.DeparturePage(curSe)
	reportsPage = ReportsPage.ReportsPage(curSe)
	mapsPage = MapsPage.MapsPage(curSe)
	mainContainer = ft.Container(content=routingPage)
	mainContainer.expand = True
	page.padding = 0

	# Add navigation to page
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

	# navigation for mobile
	if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
		page.window.width = 400
		page.navigation_bar = ft.NavigationBar(
			destinations=[ft.NavigationBarDestination(icon=ft.icons.ROUTE, label="Verbindungen"),
						  ft.NavigationBarDestination(icon=ft.icons.NEAR_ME, label="Abfahrten"),
						  ft.NavigationBarDestination(icon=ft.icons.LIST, label="Meldungen"),
						  ft.NavigationBarDestination(icon=ft.icons.MAP, label="Netzpläne")], selected_index=0,
			on_change=route_changer)
	else:
		page.window.width = 1000
		page.window.height = 600
		# navigation for desktop (enabled in common.py MyPage class)
		page.rail = ft.NavigationRail(
			selected_index=0,
			extended=True,
			destinations=[
				ft.NavigationRailDestination(icon=ft.icons.ROUTE, label="Verbindungen"),
				ft.NavigationRailDestination(icon=ft.icons.NEAR_ME, label="Abfahrten"),
				ft.NavigationRailDestination(icon=ft.icons.LIST, label="Meldungen"),
				ft.NavigationRailDestination(icon=ft.icons.MAP, label="Netzpläne"),
			],
			on_change=route_changer
		)

	# set theme type
	page.theme_mode = curSe["settings"].theme

	# update page to present
	page.add(mainContainer)
	page.update()


ft.app(main)
