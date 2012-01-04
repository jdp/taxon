#!/usr/bin/env coffee

crypto = require "crypto"
http = require "http"
_ = require "underscore"

Store  = require("../").Store

md5 = (data) ->
  crypto.createHash("md5").update(data).digest("hex")

shuffle = (o) ->
  `for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);`
  o

ITEMS = [1000, 10000, 100000]
TAGS = ["common", "uncommon", "rare", "holographic", "fire", "water", "grass"]
QUERY = {or: [{and: ["common", "fire"]}, {not: [{or: ["rare", "grass"]}]}]}
console.log "-- Using Query #{JSON.stringify(QUERY)}"
for items in ITEMS
  store = new Store
  console.log "-- Testing with #{items} items"
  start = (new Date).getTime()
  for x in [1..items]
    id = md5((Math.random() * x).toString())
    tags = shuffle(TAGS).slice(0, Math.floor(Math.random() * TAGS.length))
    store.store id, {}, tags
  end = (new Date).getTime();
  console.log "indexed #{items} items in #{end - start}ms"
  for x in [1..5]
    console.log "(cache size #{_.keys(store.cache).length})"
    start = (new Date).getTime()
    results = store.fetch QUERY
    end = (new Date).getTime()
    console.log "fetched #{results.length} items in #{end - start}ms"
  for tag of store.tag_set
    console.log "tag", tag, "has", store.tag_set[tag].items.length, "items and invalidates", store.tag_set[tag].caches.length, "caches"
