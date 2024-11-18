#!/usr/bin/env python3
# Import pyodide_http for API requests to work
import pyodide_http

pyodide_http.patch_all()

# Import flet and systems libraries
import flet as ft
import json
import os
from locales import _, set_up_locales

# Import other parts of this app
import stopsdata  # contains also the static data (#FIXME provide static as json text file)
from custom import DeparturePage, MapsPage, ReportsPage, RoutingPage
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
async def main(page: ft.Page):
	global curSe

	# basic
	page.window.title_bar_hidden = True
	page.title = "Citynav München"
	mainView = ft.View(padding=0)
	page.views.append(mainView)
	page.udt_running = False # for async process to update times in departure
	page.urt_running = False # for async process to update times in routing

	# set basic common data
	curSe["stops"] = load_stops()  # load stop data
	curSe["page"] = page
	curSe["mainView"] = mainView
	curSe["settings"] = StorageHandler(page)

	await curSe["settings"].set_up()
	set_up_locales(page, curSe)

	# Some color fixes and preferences
	# page.theme_mode = ft.ThemeMode.DARK
	page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary=ft.colors.BACKGROUND),
						  search_bar_theme=ft.SearchBarTheme(elevation=1),
						  system_overlay_style=ft.SystemOverlayStyle(status_bar_brightness=ft.Brightness.DARK,
																	 status_bar_icon_brightness=ft.Brightness.LIGHT))
	page.dark_theme = ft.theme.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary="#272a2f"),
									 text_theme=ft.TextTheme(
										 title_medium=ft.TextStyle(weight=ft.FontWeight.NORMAL, color="white")),
									 system_overlay_style=ft.SystemOverlayStyle(
										 status_bar_brightness=ft.Brightness.DARK,
										 status_bar_icon_brightness=ft.Brightness.LIGHT))

	# Add navigation to page
	def view_changer(e):
		if hasattr(e, "control"):
			index = e.control.selected_index
		else:
			index = e

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

	# setup navigations
	if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
		page.window.width = 400
		# navigation for mobile
		mainView.navigation_bar = ft.NavigationBar(
			destinations=[ft.NavigationBarDestination(icon=ft.icons.ROUTE, label=_("Connections")),
						  ft.NavigationBarDestination(icon=ft.icons.NEAR_ME, label=_("Departures")),
						  ft.NavigationBarDestination(icon=ft.icons.LIST, label=_("Disruptions")),
						  ft.NavigationBarDestination(icon=ft.icons.MAP, label=_("Maps"))], selected_index=0,
			on_change=view_changer)
		nb = mainView.navigation_bar
	else:
		page.window.width = 1000
		page.window.height = 600
		# navigation for desktop (enabled in common.py by MyPage class)
		mainView.rail = ft.NavigationRail(
			selected_index=0,
			extended=True,
			destinations=[
				ft.NavigationRailDestination(icon=ft.icons.ROUTE, label=_("Connections")),
				ft.NavigationRailDestination(icon=ft.icons.NEAR_ME, label=_("Departures")),
				ft.NavigationRailDestination(icon=ft.icons.LIST, label=_("Disruptions")),
				ft.NavigationRailDestination(icon=ft.icons.MAP, label=_("Maps")),
			],
			on_change=view_changer
		)
		nb = mainView.rail
		if page.web is False:
			mainView.decoration = ft.BoxDecoration(border=ft.border.all(2, ft.colors.ON_PRIMARY), border_radius=ft.border_radius.all(2))

	# make android back button work
	def on_pop_with_back(eventView):
		nonlocal currentIndexTracker
		currentIndex = nb.selected_index
		if mainContainer.content.currentParent:
			mainContainer.content.switch_sub(mainContainer.content.currentParent)
			currentIndexTracker = -1
		else:
			if currentIndexTracker == -1:
				currentIndexTracker = currentIndex
				view_changer(currentIndex)
			else:
				if currentIndexTracker == 0:
					page.views.pop()
					os._exit(1)
				else:
					currentIndexTracker = 0
					view_changer(0)
					nb.selected_index = 0

		page.update()

	currentIndexTracker = -1
	page.on_view_pop = on_pop_with_back

	# setup custom
	routingPage = RoutingPage.RoutingPage(curSe)
	departurePage = DeparturePage.DeparturePage(curSe)
	reportsPage = ReportsPage.ReportsPage(curSe)
	page.run_task(reportsPage.load_reports)
	mapsPage = MapsPage.MapsPage(curSe)
	mainContainer = ft.Container(content=routingPage)
	mainContainer.expand = True
	page.padding = 0

	# set theme type
	page.theme_mode = curSe["settings"].theme

	# update page to present
	mainView.controls = [mainContainer]
	page.update()


ft.app(main)
