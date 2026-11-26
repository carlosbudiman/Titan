PY ?= python3

.PHONY: help test init install doctor clean

help:
	@printf 'make install   link the CLI into ~/.local/bin and initialise state\n'
	@printf 'make test      run the full suite (no network, no model needed)\n'
	@printf 'make doctor    verify the local install\n'
	@printf 'make clean     remove caches and build artefacts\n'

install:
	./install.sh

test:
	TITAN_HOME=$$(mktemp -d) $(PY) -W ignore -m unittest discover -s tests -t .

init:
	./bin/titan init

doctor:
	./bin/titan doctor

clean:
	rm -rf __pycache__ titan/__pycache__ tests/__pycache__ .pytest_cache build dist *.egg-info
