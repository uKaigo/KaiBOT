PYTHON ?= python3

.PHONY: compile

install:
	@$(PYTHON) -m pip install -r requirements.txt

compile:
	@$(PYTHON) -m kaibot.scripts.mo_compiler
