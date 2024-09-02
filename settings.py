#!/usr/bin/env python3
#Import flet and systems librarys
import flet as ft

def page_settings(page, curSe):
    settingsView = ft.View(spacing=10)

    settingsView.appbar = ft.AppBar(
        leading=ft.Text(""),
        center_title=True,
        title=ft.Text("Mehr"),
        bgcolor=ft.colors.PRIMARY,
        color="white",
        actions=[ft.IconButton(ft.icons.CLOSE, on_click=lambda e: (page.views.pop(), page.update()))]
    )

    settingsView.controls.append(ft.Text("Einstellungen", theme_style=ft.TextThemeStyle.TITLE_MEDIUM))

    #colors
    colorDropdown =  ft.Dropdown(width=180, height=30, content_padding=ft.padding.only(right=1, left=10), options=[
        ft.dropdown.Option("Automatisch"),
        ft.dropdown.Option("Hell"),
        ft.dropdown.Option("Dunkel"),
    ], value="Automatisch")
    settingsView.controls.append(ft.Row([ft.Text("Farbschema"), colorDropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    #resultss
    def slider_changed(e):
        curSe["settings"].set_key("results", e.control.value)
        if e.control.value == 0:
            e.control.label = "Schnell"
            e.control.update()
        elif e.control.value == 1:
            e.control.label = "Ausgeglichen"
            e.control.update()
        else:
            e.control.label = "Viele"
            e.control.update()

    resultSlider = ft.Slider(
        min=0,
        max=2,
        value=curSe["settings"].results,
        divisions=2,
        label="",
        on_change=slider_changed
    )
    settingsView.controls.append(ft.Row([ft.Text("Ergebnisseanzahl"), resultSlider], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    delButton = ft.FilledButton(width=200, text="App-Daten löschen", style=ft.ButtonStyle(bgcolor=ft.colors.RED, color="white"))
    settingsView.controls.append(ft.Row([ft.Text("Zurücksetzen"), delButton], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    settingsView.controls.append(ft.Text("", size=12))

    #Donate
    settingsView.controls.append(ft.Text("Unterstützten", theme_style=ft.TextThemeStyle.TITLE_MEDIUM))
    settingsView.controls.append(ft.Text(spans=[
        ft.TextSpan("Citynav München ist "),
        ft.TextSpan("freie Software", style=ft.TextStyle(italic=True)),
        ft.TextSpan(" und steht jederzeit kostenlso zur Verfügung.\nFalls du das Projekt unterstützen möchtest freue ich mich über deine Hilfe.")
    ]))
    donateURI="donateURI"
    settingsView.controls.append(ft.Row([
        ft.Container(ft.Image(src="other/donate_de.png"), height=32, url=donateURI, url_target=ft.UrlTarget.BLANK),
        ft.Container(ft.Image(src="other/github_de.png"), height=32, url="https://github.com/", url_target=ft.UrlTarget.BLANK)
    ], alignment=ft.MainAxisAlignment.CENTER))
    settingsView.controls.append(ft.Text(spans=[
        ft.TextSpan("Um mehr über die offene Softwarelizenz zu erfahren, "),
        ft.TextSpan("klicke hier", url="https://github.com/", url_target=ft.UrlTarget.BLANK, style=ft.TextStyle(color=ft.colors.PRIMARY)),
        ft.TextSpan(".")
    ]))

    settingsView.controls.append(ft.Divider())
    settingsView.controls.append(ft.Container(ft.Text("Citynav München 0.1.0 © 2024 Manuel Ehrmanntraut", size=8, weight=ft.FontWeight.W_300), alignment=ft.alignment.center))

    page.views.append(settingsView)
    page.update()