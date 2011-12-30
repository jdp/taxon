.SUFFIXES: .coffee .js
COFFEE = coffee
SRC = lib/store.coffee lib/server.coffee main.coffee
OBJ = ${SRC:.coffee=.js}

# Stuff for compiling the PEG for simpler query language
PEGJS = pegjs
PEGSRC = lib/query_parser.pegjs

all: $(OBJ) peg

%.js: %.coffee
	$(COFFEE) -c $<

peg: $(PEGSRC)
	$(PEGJS) $< 

clean:
	-rm lib/*.js
	-rm *.js

.PHONY: all clean peg
