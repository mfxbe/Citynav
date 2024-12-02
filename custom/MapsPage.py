#!/usr/bin/env python3
# Import flet and systems libraries

import flet as ft

# Import other parts of this app
from locales import _
from common import MyPage


class MapsPage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__(_("Maps"), curSe)
		self.curSe = curSe
		curSe["map"] = ""

		# Page structure of mapsOverviewPage
		mapsOverviewPage = ft.Container()
		mapsOverview = ft.GridView(
			expand=1,
			runs_count=5,
			max_extent=150,
			child_aspect_ratio=1.0,
			spacing=5,
			run_spacing=5
		)
		mapsOverviewPage.content = mapsOverview
		self.mapsOverview = mapsOverview
		self.add_sub("mapsOverviewPage", ft.Container(mapsOverviewPage, padding=10))

		# add entries
		self.add_map_item(_("Network map city"), _("Subway, Suburban, Tram, Regional"), "lc")
		self.add_map_item(_("Network map region"), _("Subway, Suburban, Regional"), "la")
		self.add_map_item(_("Night lines city"), _("Tram, Suburban, Bus"), "nc")
		self.add_map_item(_("Transport routes city"), _("Subway, Suburban, Tram, Bus, Regional"), "mc")
		self.add_map_item(_("Transport routes region"), _("Subway, Suburban, Regional, Bus"), "ma")

		# Page structure of mapsViewPage
		#def on_pan_update(e: ft.DragUpdateEvent):
		#	e.control.top = e.control.top + e.delta_y
		#	e.control.left = e.control.left + e.delta_x
		#	e.control.update()

		#self.mapController = ft.GestureDetector(
		#	mouse_cursor=ft.MouseCursor.MOVE,
		#	on_pan_update=on_pan_update,
		#	drag_interval=10,
		#	left=-550,
		#	top=-400,
		#	content=ft.Text(""),
		#)
		self.mapController = ft.InteractiveViewer(content=ft.Text(""), boundary_margin=ft.margin.all(50), min_scale=0.5, max_scale=10, constrained=False)

		s = ft.Stack([
			ft.Container(ft.ProgressRing(width=14, height=14, color=ft.Colors.PRIMARY, stroke_width=2),
						 alignment=ft.alignment.center, left=0, right=0, top=0, bottom=0),
			self.mapController
		], expand=True)
		self.add_sub("mapsViewPage", s, "mapsOverviewPage")

	def add_map_item(self, title, description, imageName):
		def on_click_action():
			self.curSe["map"] = imageName
			self.mapController.content = ft.Image("maps/" + self.curSe["map"] + ".jpeg", width=1500)
			#self.mapController.left=-550
			#self.mapController.top=-400
			self.switch_sub("mapsViewPage")
			self.mapController.parent.update()

		item = ft.Stack([
			ft.Image(src=f"mi-placeholder.png", fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10)),
			ft.Container(
				content=ft.Text(spans=[ft.TextSpan(title + "\n", ft.TextStyle(weight=ft.FontWeight.BOLD, size=10)),
									   ft.TextSpan(description, ft.TextStyle(size=10))]),
				on_click=lambda e: on_click_action(),
				alignment=ft.alignment.bottom_left,
				padding=ft.padding.all(3), border=ft.border.all(1, ft.Colors.GREY_600),
				border_radius=ft.border_radius.all(10))
		])
		self.mapsOverview.controls.append(item)
