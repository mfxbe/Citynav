#!/usr/bin/env python3
# Import flet and systems libraries
import html
import json
import re
from datetime import datetime
from urllib.request import urlopen, Request

import flet as ft

# Import other parts of this app
from common import MyPage, color_allocator

REM_HTAG = re.compile(r'<[^>]+>')


class ReportsPage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__("Meldungen", curSe)
		self.curSe = curSe
		self.loaded = None

		listview = ft.ExpansionPanelList(expand=True, elevation=0)
		listview.expand = True
		self.listview = listview
		self.add_sub("start", ft.Container(
			content=ft.ProgressRing(width=14, height=14, color=ft.colors.PRIMARY, stroke_width=2),
			expand=True,
			alignment=ft.alignment.center))
		self.add_sub("list", ft.ListView([listview], expand=True))
		self.expand = True

	def did_mount(self):
		if self.loaded is None or (datetime.now() - self.loaded).total_seconds() > 300:
			self.switch_sub("start")
			self.update()
			self.page.run_task(self.load_reports)
			self.loaded = datetime.now()

	async def load_reports(self):
		if self.curSe["page"].web:
			proxy = "https://dyndns.mfxbe.de/other/citynav/corsproxy/proxy.php?csurl="
			req = Request(
				proxy + "https://www.mvg.de/api/ems/tickers")  # FIXME find a better way around the cors limits
		else:
			req = Request("https://www.mvg.de/api/ems/tickers")
		response = urlopen(req)
		reports = json.loads(response.read())

		con = dict()

		for r in reports:
			lineColor = "red"

			if r["type"] == "DISRUPTION":
				backColor = "#ffb800"
				fontColor = "black"
			else:
				backColor = ""
				fontColor = ""

			r["text"] = r["text"].replace("<br/>", "\n")
			r["text"] = r["text"].replace("<br>", "\n")
			r["text"] = r["text"].replace("<li>", "\n\t• ")
			r["text"] = html.unescape(REM_HTAG.sub('', r["text"]))

			ol = []
			for rl in r["lines"]:
				if r["text"] + rl["name"] not in ol:
					ol.append(r["text"] + rl["name"])
					lineColor = color_allocator(rl["name"])

					if rl["name"] in con:
						contentColumn = con[rl["name"]]
						contentColumn.controls.append(ft.Divider())
						contentColumn.controls.append(ft.Text(
							spans=[ft.TextSpan(r["title"], ft.TextStyle(size=15)), ft.TextSpan("\n" + r["text"])],
							color=fontColor))
					else:
						img = ft.Container(ft.Text(rl["name"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
										   alignment=ft.alignment.center)
						img.margin = ft.margin.only(left=10)
						contentColumn = ft.Column()
						contentColumn.controls.append(ft.Text(r["text"], color=fontColor))
						entry = ft.ExpansionPanel(header=ft.Row([img, ft.Container(ft.ListTile(
							title=ft.Text(r["title"], color=fontColor, theme_style=ft.TextThemeStyle.TITLE_MEDIUM)),
							expand=True)]),
												  content=ft.Container(contentColumn, padding=5), bgcolor=backColor,
												  can_tap_header=True)
						self.listview.controls.append(entry)
						con[rl["name"]] = contentColumn

		self.switch_sub("list")
