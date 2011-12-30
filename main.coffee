crypto  = require "crypto"
http    = require "http"
winston = require "winston"

Store  = require("./lib/store").Store
Server = require("./lib/server").Server

store  = new Store
logger = new (winston.Logger)({
  transports: [
    new (winston.transports.Console)({
      colorize:  true,
      timestamp: true
    })
  ]
})

# Some worthless benchmarks
md5 = (data) ->
  crypto.createHash("md5").update(data).digest("hex")

shuffle = (o) ->
  `for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);`
  o

ITEMS = 1000
TAGS = ["common", "uncommon", "rare", "holographic", "fire", "water", "grass"]
start = (new Date).getTime()
for x in [1..ITEMS]
  id = md5((Math.random() * x).toString())
  tags = shuffle(TAGS).slice(0, Math.floor(Math.random() * TAGS.length))
  store.store id, {}, tags
end = (new Date).getTime();
logger.debug "indexed #{ITEMS} items in #{end - start}ms"

query = {or: [{and: ["common", "fire"]}, {not: [{or: ["rare", "grass"]}]}]}
for x in [1..3]
  start = (new Date).getTime()
  results = store.fetch query
  end = (new Date).getTime()
  logger.debug "fetched #{results.length} items with #{JSON.stringify(query)} in #{end - start}ms"

server = new Server store, logger
server.start 8980
