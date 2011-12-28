.SUFFIXES: .coffee .js
COFFEE = coffee
SRC = lib/store.coffee lib/server.coffee main.coffee
OBJ = ${SRC:.coffee=.js}

all: $(OBJ)

%.js: %.coffee
	$(COFFEE) -c $<

clean:
	rm lib/*.js
	rm *.js

.PHONY: all clean
