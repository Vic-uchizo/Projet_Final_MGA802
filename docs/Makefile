# Makefile minimal pour la documentation Sphinx du projet MGA802.
# Usage : depuis le dossier docs/, lancer « make html » puis ouvrir
#         _build/html/index.html dans un navigateur.

# On utilise en priorité le Python du venv du projet (../.venv) s'il existe :
# c'est lui qui contient Sphinx. Sinon on retombe sur python3/python du PATH.
# Ainsi « make html » marche sans avoir à activer le venv au préalable.
VENV_PY     := $(wildcard ../.venv/bin/python)
PYTHON      ?= $(if $(VENV_PY),$(VENV_PY),$(shell command -v python3 || command -v python))
SPHINXBUILD ?= $(PYTHON) -m sphinx
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: help html clean

help:
	@echo "make html   - construit la documentation HTML dans _build/html"
	@echo "make clean   - supprime le dossier _build"

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"
	@echo "Documentation générée : $(BUILDDIR)/html/index.html"

clean:
	rm -rf "$(BUILDDIR)"
