#!/usr/bin/env python3
# Import flet and systems libraries
import flet as ft

# Import other parts of this app
import StationSearchBar


class RoutingPage(ft.AnimatedSwitcher):
	def __init__(self, curSe):
		# basics
		c = ft.Column()
		super().__init__(c)

		positionSearchBar = StationSearchBar.StationSearchBar(hint="Haltestelle", stations=curSe["stops"])
		c.controls.append(ft.Container(positionSearchBar, alignment=ft.alignment.center))

		goButton = ft.FilledButton(text="los anzeigen", expand=True, on_click=lambda e: print("Test"),
								   style=ft.ButtonStyle(bgcolor="#36618e", color="white"))
		c.controls.append(ft.Row(controls=[goButton]))

		c.controls.append(ft.Row())
		historyHeader = ft.Text("Verlauf", weight=ft.FontWeight.BOLD)
		c.controls.append(ft.Row(controls=[historyHeader]))