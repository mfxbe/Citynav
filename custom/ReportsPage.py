#!/usr/bin/env python3
# Import flet and systems libraries
import html
import json
import re
from datetime import datetime
from urllib.request import urlopen, Request

import flet
import flet as ft

# Import other parts of this app
from locales import _
from common import MyPage, color_allocator

REM_HTAG = re.compile(r'<[^>]+>')


class ReportsPage(MyPage):
	def __init__(self, curSe):
		# basics
		super().__init__(_("Disruptions"), curSe)
		self.curSe = curSe
		self.loaded = None
		self.curSe["rps"] = dict()

		listview = ft.ExpansionPanelList(expand=True, elevation=0, expand_icon_color=ft.colors.PRIMARY,
		                                 expanded_header_padding=ft.padding.symmetric(vertical=8.0))
		listview.expand = True
		self.listview = listview
		self.add_sub("start", ft.Container(
			content=ft.ProgressRing(width=14, height=14, color=ft.colors.PRIMARY, stroke_width=2),
			expand=True,
			alignment=ft.alignment.center))
		self.add_sub("list", ft.ListView([listview], expand=True))
		self.expand = True
		self.switch_sub("start")

	def did_mount(self):
		self.switch_sub("start")
		self.update()
		if self.loaded is None or (datetime.now() - self.loaded).total_seconds() > 300:
			self.update()
			self.page.run_task(self.load_reports)
			self.loaded = datetime.now()
		else:
			self.switch_sub("list")

	async def load_reports(self):
		# clear
		self.listview.controls.clear()

		con = dict()
		p = 1

		# s-bahn (only current disruptions because these are currently not part of the mvg api)
		if self.curSe["page"].web:
			proxy = "https://dyndns.mfxbe.de/other/citynav/corsproxy/proxy.php?csurl="
			sReq = Request(
				proxy + "https://www.s-bahn-muenchen.de/.rest/verkehrsmeldungen?path=%2Faktuell%2Fbayern%26filter=true%26channel=REGIONAL%26prop=SBAHN%26states=BY%26authors=S_BAHN_MUC")  # FIXME find a better way around the cors limits
		else:
			sReq = Request(
				"https://www.s-bahn-muenchen.de/.rest/verkehrsmeldungen?path=%2Faktuell%2Fbayern&filter=true&channel=REGIONAL&prop=SBAHN&states=BY&authors=S_BAHN_MUC")
		sBahnResponse = urlopen(sReq)
		sBahnReports = json.loads(sBahnResponse.read())

		for r in sBahnReports["disruptions"]:
			r["text"] = r["text"].replace("<br/>", "\n")
			r["text"] = r["text"].replace("<br>", "\n")
			r["text"] = r["text"].replace("<li>", "\n\t• ")
			r["text"] = r["text"].replace("<p>", "\n")
			r["text"] = r["text"].replace("\n", "", 1)
			r["text"] = html.unescape(REM_HTAG.sub('', r["text"]))

			# try filtering out non disruption reports because these are already in mvg api response
			# todo there are probably more cases to handle here
			if r["cause"]["category"] == "construction" and not r["topDisruption"]:
				continue

			for l in r["lines"]:
				l["name"] = l["name"].replace(" ", "")

				if l["property"] == "SBAHN":
					if l["name"] in con:
						contentColumn = con[l["name"]]
						contentColumn.controls.append(ft.Divider())
						text = ft.Text(
							spans=[ft.TextSpan(r["headline"] + "\n", ft.TextStyle(size=16)),
							       ft.TextSpan("\n" + r["text"])],
							color="black")
						contentColumn.controls.append(text)
					else:
						lineColor = color_allocator(l["name"])
						if l["name"].startswith("S"):
							if l["name"].startswith("S8"):
								c = "#f2c531"
							else:
								c = ft.colors.WHITE
							img = ft.Container(ft.Text(l["name"], color=c), bgcolor=lineColor, width=35,
							                   alignment=ft.alignment.center, border_radius=10)
						else:
							img = ft.Container(ft.Text(l["name"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
							                   alignment=ft.alignment.center)
						img.margin = ft.margin.only(left=10)

						contentColumn = ft.Column(alignment=ft.alignment.center_left, expand=True)
						text = ft.Text(r["text"], color="black")
						contentColumn.controls.append(text)
						entry = ft.ExpansionPanel(header=ft.Row([img,
						                                         ft.Container(ft.Text(r["headline"].replace("\n", ""),
						                                                              color="black",
						                                                              theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
						                                                      expand=True,
						                                                      padding=ft.padding.all(15)
						                                                      )]
						                                        ),
						                          content=ft.Container(contentColumn,
						                                               padding=ft.padding.only(left=5, top=5, right=5,
						                                                                       bottom=20),
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

		# mvg
		#  if self.curSe["page"].web:
		# 	proxy = "https://dyndns.mfxbe.de/other/citynav/corsproxy/proxy.php?csurl="
		#	req = Request(
		#		proxy + "https://www.mvg.de/api/bgw-pt/v3/messages")  # FIXME find a better way around the cors limits
		# else:
		req = Request("https://www.mvg.de/api/bgw-pt/v3/messages")
		response = urlopen(req)
		reports = json.loads(response.read())

		for r in reports:
			lineColor = "red"

			if r["type"] == "INCIDENT":
				backColor = "#ffb800"
				fontColor = "black"
			else:
				backColor = ""
				fontColor = ""

			r["description"] = r["description"].replace("<br/>", "\n")
			r["description"] = r["description"].replace("<br>", "\n")
			r["description"] = r["description"].replace("<li>", "\n\t• ")
			r["description"] = html.unescape(REM_HTAG.sub('', r["description"]))
			if r["description"][0] == " ":
				r["description"] = r["description"][1:]

			ol = []

			for rl in r["lines"]:

				# sort out line numbers bigger than 200 (buses outside of munich) there are so many reports there
				# so this is for a better overview. In future todo: a setting to enable if needed
				if int(re.sub(r'\D', '', rl["label"])) >= 200:
					continue

				if r["description"] + rl["label"] not in ol:
					ol.append(r["description"] + rl["label"])
					lineColor = color_allocator(rl["label"])

					if rl["label"] in con:
						contentColumn = con[rl["label"]]

						# if disruption then allways black font color and not the defined one from above
						if hasattr(contentColumn.controls[0], "myIsCurrent"):
							uFontColor = "black"
						else:
							uFontColor = fontColor

						contentColumn.controls.append(ft.Divider(color=uFontColor))

						text = ft.Text(
							spans=[ft.TextSpan(r["title"] + "\n", ft.TextStyle(size=15)),
							       ft.TextSpan("\n" + r["description"])],
							color=uFontColor, expand=True)
						contentColumn.controls.append(text)
					else:
						img = ft.Container(ft.Text(rl["label"], color=ft.colors.WHITE), bgcolor=lineColor, width=35,
						                   alignment=ft.alignment.center)
						img.margin = ft.margin.only(left=10)
						contentColumn = ft.Column(alignment=ft.alignment.center_left, expand=True)
						text = ft.Text(r["description"], color=fontColor, expand=True)
						contentColumn.controls.append(text)
						entry = ft.ExpansionPanel(
							header=ft.Row([img,
							               ft.Container(ft.Text(r["title"],
							                                    color=fontColor,
							                                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
							                            expand=True,
							                            padding=ft.padding.all(15)
							                            )]
							              ),
							content=ft.Container(contentColumn,
							                     padding=ft.padding.only(left=5, top=5, right=5, bottom=20)),
							bgcolor=backColor,
							can_tap_header=True
						)
						self.listview.controls.append(entry)
						con[rl["label"]] = contentColumn

						if r["type"] == "INCIDENT":
							text.myIsCurrent = True
							self.curSe["rps"][rl["label"]] = entry
							p = len(self.listview.controls)

		self.switch_sub("list")
