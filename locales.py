#!/usr/bin/env python3
import locale
import importlib

try:
	l = locale.getlocale()[0][:2]
	myl10n = importlib.import_module('locales_data.' + l)
except:
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