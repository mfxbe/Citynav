#!/usr/bin/env python3
# Import flet and systems librarys
import flet as ft

from locales import _


def page_settings(page, curSe):

	if page.platform is ft.PagePlatform.IOS or page.platform is ft.PagePlatform.ANDROID:
		settingsViewConstruct = ft.View(spacing=10)
		settingsViewConstruct.appbar = ft.AppBar(
			leading=ft.Text(""),
			center_title=True,
			title=ft.Text(_("More")),
			bgcolor="#36618e",
			color="white",
			actions=[ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: (page.views.pop(), page.update()))]
		)
		page.views.append(settingsViewConstruct)
		settingsView = ft.Column(spacing=10)
		sVC = ft.Container(settingsView)
		sVC.theme = ft.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary="#272a2f"))
		settingsViewConstruct.controls.append(sVC)
	else:
		settingsView = ft.Column(spacing=10)
		sVC = ft.Container(settingsView)
		sVC.theme = ft.Theme(color_scheme=ft.ColorScheme(primary="#36618e", on_tertiary="#272a2f"))
		sVC.dark_theme = sVC.theme
		tR = ft.Row([
			ft.Text(_("More")),
			ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: page.close(settingsDialog))
		], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
		settingsDialog = ft.AlertDialog(title=tR, content=sVC)
		page.open(settingsDialog)

	settingsView.controls.append(ft.Text(_("Preferences"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM))

	# language
	def lang_dropdown_changed(e):
		if e.control.value == "Deutsch":
			value = "de"
		elif e.control.value == "English":
			value = "en"
		elif e.control.value == "Italiano":
			value = "it"
		else:
			value = "unset"
		curSe["settings"].set_key("language", value)
		snBar = ft.SnackBar(ft.Text(_("Restart app to finish language change.")))
		curSe["page"].overlay.append(snBar)
		snBar.open = True
		curSe["page"].update()

	languageDropdown = ft.DropdownM2(width=180, height=30, content_padding=ft.padding.only(right=1, left=10), options=[
		ft.dropdown.Option("Deutsch"),
		ft.dropdown.Option("English"),
		ft.dropdown.Option("Italiano")
	], value="unset")

	if "en" in curSe["settings"].language:
		languageDropdown.value = "English"
	elif "it" in curSe["settings"].language:
		languageDropdown.value = "Italiano"
	else:
		languageDropdown.value = "Deutsch"

	settingsView.controls.append(
		ft.Row([ft.Text(_("Language")), languageDropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
	languageDropdown.on_change = lang_dropdown_changed


	# colors
	def dropdown_changed(e):
		if e.control.value == _("Automatic"):
			value = "auto"
		elif e.control.value == _("Light"):
			value = "light"
		else:
			value = "dark"

		curSe["settings"].set_key("theme", value)
		curSe["page"].theme_mode = curSe["settings"].theme  # set theme according to new setting
		curSe["page"].mainContainer.theme_mode = curSe["settings"].theme  # set theme according to new setting
		curSe["page"].update()

	colorDropdown = ft.DropdownM2(width=180, height=30, content_padding=ft.padding.only(right=1, left=10), options=[
		ft.dropdown.Option(_("Automatic")),
		ft.dropdown.Option(_("Light")),
		ft.dropdown.Option(_("Dark")),
	], value=_("Automatic"))

	if curSe["settings"].theme == "auto":
		colorDropdown.value = _("Automatic")
	elif  curSe["settings"].theme == "light":
		colorDropdown.value = _("Light")
	else:
		colorDropdown.value = _("Dark")

	settingsView.controls.append(
		ft.Row([ft.Text(_("Color scheme")), colorDropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
	colorDropdown.on_change = dropdown_changed

	# results
	def slider_changed(e):
		curSe["settings"].set_key("results", int(e.control.value))
		if e.control.value == 0:
			e.control.label = _("Fast")
			e.control.update()
		elif e.control.value == 1:
			e.control.label = _("Balanced")
			e.control.update()
		else:
			e.control.label = _("Many")
			e.control.update()

	resultSlider = ft.Slider(
		min=0,
		max=2,
		value=curSe["settings"].results,
		divisions=2,
		label="",
		on_change=slider_changed
	)
	settingsView.controls.append(
		ft.Row([ft.Text(_("Results")), resultSlider], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

	# colors
	def messages_dropdown_changed(e):
		if e.control.value == _("Current"):
			value = "current"
		else:
			value = "all"

		curSe["settings"].set_key("messages_show", value)

	messagesDropdown = ft.DropdownM2(width=180, height=30, content_padding=ft.padding.only(right=1, left=10), options=[
		ft.dropdown.Option(_("Current")),
		ft.dropdown.Option(_("All")),
	], value=_("Current"))

	if curSe["settings"].messages_show == "all":
		messagesDropdown.value = _("All")

	settingsView.controls.append(
		ft.Row([ft.Text(_("Reports in connections")), messagesDropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
	messagesDropdown.on_change = messages_dropdown_changed

	# more
	def stop_checkbox_changed(e):
		if e.data == "true":
			curSe["settings"].set_key("stops_shown", True)
		else:
			curSe["settings"].set_key("stops_shown", False)
	settingsView.controls.append(
		ft.Row([ft.Text(_("Show stop position")), ft.Checkbox(value=curSe["settings"].stops_shown, width=200, on_change=stop_checkbox_changed)],
			   alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

	def reset_app(_b):
		curSe["settings"].reset_all()

	delButton = ft.FilledButton(width=200, text=_("Delete app data"),
								style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color="white"))
	settingsView.controls.append(
		ft.Row([ft.Text(_("Reset")), delButton], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
	delButton.on_click = reset_app

	settingsView.controls.append(ft.Text("", size=12))

	# Donate
	settingsView.controls.append(ft.Text(_("Support"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM))
	settingsView.controls.append(ft.Text(spans=[
		ft.TextSpan("Citynav München " + _("is ")),
		ft.TextSpan(_("free software"), style=ft.TextStyle(italic=True)),
		ft.TextSpan(
			_(", you can use, share and change it. You\nare also welcome to support the development."))
	]))
	donateURI = "https://liberapay.com/mfxbe/donate"
	# settingsView.controls.append(ft.Row([
	#	ft.Container(ft.Image(src="other/donate_de.png"), height=32, url=donateURI, url_target=ft.UrlTarget.BLANK),
	#	ft.Container(ft.Image(src="other/github_de.png"), height=32, url="https://github.com/mfxbe/Citynav",
	#				 url_target=ft.UrlTarget.BLANK)
	# ], alignment=ft.MainAxisAlignment.CENTER))
	settingsView.controls.append(ft.Text(spans=[
		ft.TextSpan(_("To find out more about the public software licence, ")),
		ft.TextSpan(_("click here"), url="https://github.com/mfxbe/Citynav/blob/master/LICENSE.md", url_target=ft.UrlTarget.BLANK,
					style=ft.TextStyle(color=ft.Colors.PRIMARY)),
		ft.TextSpan(".")
	]))

	# settingsView.controls.append(ft.Divider())
	settingsView.controls.append(
		ft.Container(ft.Text("Citynav München 0.1.0 © 2024 Manuel Ehrmanntraut", size=8, weight=ft.FontWeight.W_300),
					 alignment=ft.alignment.center))

	page.update()
