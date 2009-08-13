PYTHON ?= python

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
	pylint --include-ids=y --max-line-length=120 --disable-msg=W0621,W0622,C0103 \
		--reports=no dirvish-stats 2>/dev/null || true
	@pylint --include-ids=y --max-line-length=120 --disable-msg=W0621,W0622,C0103 \
		dirvish-stats 2>/dev/null |tail -n5

clean:
	@for i in $(MANPAGES); do \
		rm -f $$i.html $$i.xml $$i.gz; done
