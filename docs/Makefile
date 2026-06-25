# Makefile minimal pour la documentation Sphinx du projet MGA802.
# Usage : depuis le dossier docs/, lancer « make html » puis ouvrir
#         _build/html/index.html dans un navigateur.

SPHINXBUILD ?= python -m sphinx
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
