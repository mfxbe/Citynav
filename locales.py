#!/usr/bin/env python3
import locale
import importlib
from urllib.parse import urlparse, parse_qs

import flet as ft

myl10n = lambda: None
myl10n.data = dict()

# support multiple languages (would prefer gettext for that by I do not manage to get it working in web & android builds)
# this small modul is written in a way easily replaceable by gettext
# todo replace with gettext
def _(string):
	global myl10n

	if string in myl10n.data:
		return myl10n.data[string]
	else:
		return string

def set_up_locales(page, curSe):
	global myl10n
	l = None

	# there is no way on Android to get the current system language, use "de" because its most likely the correct one
	if page.platform == ft.PagePlatform.ANDROID:
		l = "de"

	if curSe["settings"].language is not "unset":
		l = curSe["settings"].language

	try:
		if l is None:
			l = locale.getlocale()[0][:2]
		if l is None:
			l = "de"
		myl10n = importlib.import_module('locales_data.' + l)
	except Exception as e:
		print("s " + str(e))
		myl10n.data = dict()