PYTHON ?= python
PYLINT_IGNORE = "W0603,W0621,W06022,C0103"

%.html : %.txt ;
	asciidoc -b xhtml11 $^

%.gz : %.txt ;
	a2x -f manpage $^ 2>&1 |grep -v '^Note: ' >&2
	gzip -f --best $(patsubst %.txt,%, $^)

MANPAGES = $(patsubst %.txt,%,$(wildcard *.txt))

all: doc

doc: doc_man doc_html
doc_html: $(addsuffix .html, $(MANPAGES))
doc_man: $(addsuffix .gz, $(MANPAGES))

test:
	cd tests && ${PYTHON} dirvish-stats_test.py

testv:
	cd tests && ${PYTHON} dirvish-stats_test.py -v

check:
	@echo "Ignoring the folloing messages:"
	@echo "    W0603 - Using global statement"
	@echo "    W0621 - Redefining variable from outer scope"
	@echo "    W0622 - Redefining built-in"
	@echo "    C0103 - Invalid name, (should match [a-z_][a-z0-9_]{2,30}$$)"
	@echo
	pylint --include-ids=y --max-line-length=120 --disable-msg=${PYLINT_IGNORE} \
		--reports=no dirvish-stats 2>/dev/null || true
	@pylint --include-ids=y --max-line-length=120 --disable-msg=${PYLINT_IGNORE} \
		dirvish-stats 2>/dev/null |tail -n5

clean:
	@for i in $(MANPAGES); do \
		rm -f $$i.html $$i.xml $$i.gz; done
