PYTHON ?= python3

.PHONY: install compile gettext

install:
	@$(PYTHON) -m pip install -r requirements.txt

compile:
	@$(PYTHON) -m kaibot.scripts.mo_compiler

gettext:
	@$(PYTHON) -m dpygettext kaibot --omit-empty -rVcRm
