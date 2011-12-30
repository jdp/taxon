_ = require "underscore"

tuplize = () ->
  Array.prototype.slice.call(arguments).sort().join(";")

fastintersection = (set1, set2) ->
  set = {}
  larger_set = if (set1.length > set2.length) then set1 else set2
  smaller_set = if (set1.length > set2.length) then set2 else set1
  for m in larger_set
    set[m] = 1
  for m in smaller_set
    if m of set
      set[m] = set[m] + 1
  return _.filter _.keys(set), (key) ->
    set[key] > 1

fastunion = (set1, set2) ->
  set = {}
  for m in set1
    set[m] = 1
  for m in set2
    set[m] = 1
  return _.keys(set)

fastdifference = (set1, set2) ->
  set = {}
  for m in set1
    set[m] = 1
  for m in set2
    if m of set
      set[m] = set[m] - 1
  return _.filter _.keys(set), (key) ->
    set[key] == 1

class QueryError extends Error
  constructor: (value) ->
    @value = value
    @name = "QueryError"

  toString: ->
    "#{@name}: #{@value}"

class Store
  item_set: {}
  tag_set: {}
  and_set: {}
  or_set: {}
  not_set: {}

  store: (id, data, tags) ->
    tags = _.uniq tags
    item = { _id: id, data: data, tags: tags }
    @item_set[id] = item
    # Keep a master collection of tags
    for tag in tags
      unless tag of @tag_set
        @tag_set[tag] =
          dirty:
            or: false
            not: false
          items: []
      # Once a tag set is dirtied, it is re-indexed on next query
      @tag_set[tag].dirty = { or: true, not: true }
      @tag_set[tag].items.push id
    # We can index AND relations at insert time
    for tag_a in tags
      for tag_b in tags
        unless tag_a == tag_b
          bucket = tuplize(tag_a, tag_b)
          @and_set[bucket] = [] unless bucket of @and_set
          @and_set[bucket].push id

  and_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("and operation requires 2 arguments")) if args.length != 2
    [q1, q2] = args
    if _.isString(q1) and _.isString(q2)
      if q1 == q2
        if q1 of @tag_set then @tag_set[q1].items else []
      else
        bucket = tuplize(q1, q2)
        return [] unless bucket of @and_set
        @and_set[bucket]
    else
      return fastintersection @fetch(q1), @fetch(q2)

  or_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("or operation requires 2 arguments")) if args.length != 2
    [q1, q2] = args
    if _.isString(q1) and _.isString(q2)
      if q1 == q2
        if q1 of @tag_set then @tag_set[q1].items else []
      else
        bucket = tuplize(q1, q2)
        if @tag_set[q1].dirty.or or @tag_set[q2].dirty.or
          @or_set[bucket] = [] unless bucket of @or_set
          unfiltered = @tag_set[q1].items.concat(@tag_set[q2].items)
          filtered = {}
          for item in unfiltered
            filtered[item] = 0
          @or_set[bucket] = _.keys(filtered)
          @tag_set[q1].dirty.or = false
          @tag_set[q2].dirty.or = false
        @or_set[bucket]
    else
      return fastunion @fetch(q1), @fetch(q2)

  not_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("not operation requires 1 argument")) if args.length != 1
    [q1] = args
    if _.isString(q1)
      if q1 in _.keys(@tag_set)
        if @tag_set[q1].dirty.not
          tags = fastdifference _.keys(@tag_set), [q1]
          sets = _.map tags, (tag) => @tag_set[tag].items
          @not_set[q1] = _.reduce sets, (memo, set) -> fastunion(memo, set)
          @tag_set[q1].dirty.not = false
        @not_set[q1]
      else
        []
    else
      fastdifference _.keys(@item_set), @fetch(q1)
        
  fetch: (query) ->
    if _.isString query
      @tag_set[query].items
    else if "and" of query
      @and_fetch.apply this, query.and
    else if "or" of query
      @or_fetch.apply this, query.or
    else if "not" of query
      @not_fetch.apply this, query.not
    else
      []

  find: (query) ->
    _.map @fetch(query), (result) => @item_set[result]

module.exports =
  QueryError: QueryError
  Store: Store
