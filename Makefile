#-*- coding: utf-8 -*-
#:Progetto:  nssjson
#:Creato:    mer 19 mar 2014 11:39:41 CET
#:Autore:    Lele Gaifax <lele@metapensiero.it>
#:Licenza:   MIT
#

PYTHON := $(BINDIR)python
BUMPER := bump_version
VERSION_TXT := version.txt
VERSION = $(shell cat $(VERSION_TXT))

.PHONY: bump-minor-version
bump-minor-version:
	$(BUMPER) $(VERSION_TXT)

.PHONY: bump-major-version
bump-major-version:
	$(BUMPER) --major $(VERSION_TXT)

.PHONY: assert-clean-tree
assert-clean-tree:
	@(test -z "$(shell git status -s --untracked=no)" || \
	  (echo "UNCOMMITTED STAFF" && false))

.PHONY: assert-nssjson-branch
assert-nssjson-branch:
	@(test "$(shell git rev-parse --abbrev-ref HEAD)" = "nssjson" || \
	  (echo "NOT IN NSSJSON BRANCH" && false))

.PHONY: release
release: assert-nssjson-branch assert-clean-tree
	$(MAKE) bump-minor-version
	@echo ">>>"
	@echo ">>> Do your duties (update CHANGES.rst for example), then"
	@echo ">>> execute “make tag-release”."
	@echo ">>>"

.PHONY: major-release
major-release: assert-nssjson-branch assert-clean-tree
	$(MAKE) bump-major-version
	@echo ">>>"
	@echo ">>> Do your duties (update CHANGES.rst for example), then"
	@echo ">>> execute “make tag-release”."
	@echo ">>>"

.PHONY: tag-release
tag-release: assert-nssjson-branch test-readme+changes-markup
	git commit -a -m "Release $(VERSION)"
	git tag -a -m "Version $(VERSION)" nssjson_v$(VERSION)

.PHONY: test-readme+changes-markup
test-readme+changes-markup:
	@[ `(cat README.rst; echo; cat CHANGES.rst) \
	    | rst2html.py 2>&1 >/dev/null \
	    | wc -l` -eq 0 ] \
	  || (echo "ERROR: README+CHANGES rst markup check failed!"; exit 1)
	@fgrep -qi unreleased CHANGES.rst \
	  && (echo "ERROR: release date not set in CHANGES.rst"; exit 1) \
	  || true

.PHONY: pypi-upload
pypi-upload: assert-nssjson-branch assert-clean-tree
	$(PYTHON) setup.py sdist upload

.PHONY: publish
publish: pypi-upload
	git push
	git push --tags
