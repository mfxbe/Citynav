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
		self.curSe["rps"] = dict()

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
		self.switch_sub("start")
		if self.loaded is None or (datetime.now() - self.loaded).total_seconds() > 300:
			self.update()
			self.page.run_task(self.load_reports)
			self.loaded = datetime.now()
		else:
			self.switch_sub("list")

	async def load_reports(self):
		#clear
		self.listview.controls.clear()

		# mvg
		if self.curSe["page"].web:
			proxy = "https://dyndns.mfxbe.de/other/citynav/corsproxy/proxy.php?csurl="
			req = Request(
				proxy + "https://www.mvg.de/api/ems/tickers")  # FIXME find a better way around the cors limits
		else:
			req = Request("https://www.mvg.de/api/ems/tickers")
		response = urlopen(req)
		reports = json.loads(response.read())

		con = dict()
		p = 1

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
						text = ft.Text(
							spans=[ft.TextSpan(r["title"] + "\n", ft.TextStyle(size=16)), ft.TextSpan("\n" + r["text"])],
							color=fontColor, expand=True)
						contentColumn.controls.append(text)
					else:
						img = ft.Container(ft.Text(rl["name"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
										   alignment=ft.alignment.center)
						img.margin = ft.margin.only(left=10)
						contentColumn = ft.Column()
						text = ft.Text(r["text"], color=fontColor, expand=True)
						contentColumn.controls.append(text)
						entry = ft.ExpansionPanel(header=ft.Row([img, ft.Container(ft.ListTile(
							title=ft.Text(r["title"], color=fontColor, theme_style=ft.TextThemeStyle.TITLE_MEDIUM)),
							expand=True)]),
												  content=ft.Container(contentColumn, padding=5), bgcolor=backColor,
												  can_tap_header=True)
						self.listview.controls.append(entry)
						con[rl["name"]] = contentColumn

						if r["type"] == "DISRUPTION":
							text.myIsCurrent = True
							self.curSe["rps"][rl["name"]] = entry
							p = len(self.listview.controls)

		# s-bahn (only current disruptions)
		if self.curSe["page"].web:
			proxy = "https://dyndns.mfxbe.de/other/citynav/corsproxy/proxy.php?csurl="
			sReq = Request(
				proxy + "https://www.s-bahn-muenchen.de/.rest/verkehrsmeldungen?path=%2Faktuell%26filter=false%26channel=REGIONAL%26prop=REGIONAL%26states=BY%26authors=S_BAHN_MUC")  # FIXME find a better way around the cors limits
		else:
			sReq = Request("https://www.s-bahn-muenchen.de/.rest/verkehrsmeldungen?path=%2Faktuell&filter=false&channel=REGIONAL&prop=REGIONAL&states=BY&authors=S_BAHN_MUC")
		sBahnResponse = urlopen(sReq)
		sBahnReports = json.loads(sBahnResponse.read())

		for r in sBahnReports["disruptions"]:
			r["text"] = r["text"].replace("<br/>", "\n")
			r["text"] = r["text"].replace("<br>", "\n")
			r["text"] = r["text"].replace("<li>", "\n\t• ")
			r["text"] = html.unescape(REM_HTAG.sub('', r["text"]))

			for l in r["lines"]:
				l["name"] = l["name"].replace(" ", "")

				if l["property"] == "SBAHN":
					if l["name"] in con:
						contentColumn = con[l["name"]]
						contentColumn.controls.append(ft.Divider())
						text = ft.Text(
							spans=[ft.TextSpan(r["summary"] + "\n", ft.TextStyle(size=16)), ft.TextSpan("\n" + r["text"])],
							color="black")
						contentColumn.controls.append(text)
					else:
						lineColor = color_allocator(l["name"])

						img = ft.Container(ft.Text(l["name"], color=ft.colors.WHITE),
										   bgcolor=lineColor, width=35,
										   alignment=ft.alignment.center)
						img.margin = ft.margin.only(left=10)
						contentColumn = ft.Column(alignment=ft.alignment.center_left, expand=True)
						text = ft.Text(r["text"], color="black")
						contentColumn.controls.append(text)
						entry = ft.ExpansionPanel(header=ft.Row([img, ft.Container(ft.ListTile(
							title=ft.Text(r["summary"].replace("\n", ""), color="black", theme_style=ft.TextThemeStyle.TITLE_MEDIUM)),
							expand=True)]),
												  content=ft.Container(contentColumn, padding=5,
																	   alignment=ft.alignment.center_left),
												  bgcolor="#ffb800",
												  can_tap_header=True)
						self.listview.controls.insert(p, entry)
						p = p + 1

						con[l["name"]] = contentColumn
						self.curSe["rps"][l["name"]] = entry

					text.myIsCurrent = True
				else:
					cL = l
					cL["property"] = "SBAHN"
					cL["name"] = "S" + r["headline"][2]
					r["lines"].append(cL)

		self.switch_sub("list")
