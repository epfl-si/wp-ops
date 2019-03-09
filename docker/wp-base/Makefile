# The latest version of plugins.csv can be pulled out of a Google Sheet.

GOOGLE_DOC_KEY=1pfUbu0vE-0vDA6XC7bSC_hgz497JT3E95DkdhGiAz2Y
GOOGLE_SHEET_GID="Plug-ins%20dans%20l%27image"

.PHONY: clean all
all: plugins.csv
clean:
	-rm plugins.csv

# https://stackoverflow.com/a/33727897/435004
plugins.csv:
	curl "https://docs.google.com/spreadsheets/d/$(GOOGLE_DOC_KEY)/gviz/tq?tqx=out:csv&sheet=$(GOOGLE_SHEET_GID)" | \
	  ./filter-google-csv.pl 'Plug-in' 'Emplacement' > $@
