crypto = require "crypto"
_ = require "underscore"

_.isLiteral = (val) ->
  (val is null) or ("object" isnt typeof(val))

tuplize = () ->
  Array.prototype.slice.call(arguments).sort().join(";")

sha1 = (data) ->
  crypto.createHash("sha1").update(data).digest("hex")

deepcopy = (obj) ->
  if _.isLiteral(obj)
    return obj
  if _.isArray(obj)
    return _.map(obj, (val) -> deepcopy(val))
  if (obj instanceof Object)
    copy = {}
    for key of obj
      if obj.hasOwnProperty(key)
        copy[key] = deepcopy(obj[key])
    return copy
  throw new Error("Unable to deep copy object #{obj}")

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

class CachedQuery
  constructor: (fn, args, tags) ->
    @fn = fn
    @args = args
    @tags = tags or []
    @bucket = "$#{sha1(@getBucket())}"

  getBucket: ->
    args = _.map @args, (arg) -> "#{arg}"
    "#{@fn}:#{args.join(';')}"

  allTags: ->
    tags = _.map @args, (arg) ->
      if _.isString(arg)
        arg
      else
        arg.allTags()
    _.uniq(_.flatten(tags))
    
  toString: ->
    @bucket

class Store
  constructor: ->
    @item_set = {}
    @tag_set = {}
    @cache = {}
    @cache_tree = {}

  store: (id, data, tags) ->
    tags = _.uniq tags
    item =
      _id: id
      data: data
      tags: tags
    # Make each item quickly retrieveable by ID
    @item_set[id] = item
    # Keep a master collection of tags
    for tag in tags
      unless tag of @tag_set
        @tag_set[tag] =
          items: []
          caches: []
      # Add the item ID to the list that each tag keeps
      @tag_set[tag].items.push id
      # Invalidate the caches that the tag affects
      for bucket in @tag_set[tag].caches
        delete @cache[bucket]

  prune_query: (root) ->
    if _.isLiteral(root) or _.isArray(root) or (root instanceof CachedQuery)
      root
    else
      fn = _.keys(root)[0]
      cache_eligible = _.all root[fn], (arg) ->
        _.isString(arg) or (arg instanceof CachedQuery)
      if cache_eligible
        tags = _.filter root[fn], _.isString
        cached_query = new CachedQuery(fn, root[fn])
        bucket = cached_query.toString()
        if bucket of @cache
          cached_query
        else
          root
      else
        root

  visit_query: (root) ->
    if _.isLiteral(root) or (root instanceof CachedQuery)
      root
    else if _.isArray(root)
      for i in [0..root.length-1]
        @visit_query root[i]
        root[i] = @prune_query(root[i])
    else
      for fn of root
        @visit_query root[fn]
        root[fn] = @prune_query(root[fn])

  optimize_query: (query) ->
    if _.isLiteral(query)
      query
    else
      new_query = {$wrap: deepcopy(query)}
      @visit_query new_query
      new_query.$wrap

  and_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("and operation requires 2 arguments")) if args.length != 2
    [q1, q2] = args
    if (_.isString(q1) or (q1 instanceof CachedQuery)) and (_.isString(q2) or (q2 instanceof CachedQuery))
      results = if q1 == q2
        if q1 of @tag_set then @tag_set[q1].items else []
      else
        fastintersection @_fetch(q1), @_fetch(q2)
      tags = _.filter(args, _.isString)
      cached = new CachedQuery "and", args, tags
      bucket = cached.toString()
      @cache[bucket] = results
      for tag in cached.allTags()
        @tag_set[tag].caches.push bucket
      results
    else
      fastintersection @_fetch(q1), @_fetch(q2)
    
  or_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("or operation requires 2 arguments")) if args.length != 2
    [q1, q2] = args
    if (_.isString(q1) or (q1 instanceof CachedQuery)) and (_.isString(q2) or (q2 instanceof CachedQuery))
      results = if q1 == q2
        if q1 of @tag_set then @tag_set[q1].items else []
      else
        fastunion @_fetch(q1), @_fetch(q2)
      tags = _.filter(args, _.isString)
      cached = new CachedQuery "or", args, tags
      bucket = cached.toString()
      @cache[bucket] = results
      for tag in cached.allTags()
        @tag_set[tag].caches.push bucket
      results
    else
      fastunion @_fetch(q1), @_fetch(q2)

  not_fetch: () ->
    args = Array.prototype.slice.call(arguments)
    throw (new QueryError("not operation requires 1 argument")) if args.length != 1
    [q1] = args
    if (_.isString(q1) or (q1 instanceof CachedQuery))
      results = fastdifference(_.keys(@item_set), @_fetch(q1))
      tags = _.filter(args, _.isString)
      cached = new CachedQuery "not", args, tags
      bucket = cached.toString()
      @cache[bucket] = results
      for tag in cached.allTags()
        @tag_set[tag].caches.push bucket
      results
    else
      fastdifference(_.keys(@item_set), @_fetch(q1))

  _fetch: (query) ->
    if query instanceof CachedQuery
      return @cache[query.toString()]
    if _.isString(query)
      @tag_set[query].items
    else if "and" of query
      @and_fetch.apply this, query.and
    else if "or" of query
      @or_fetch.apply this, query.or
    else if "not" of query
      @not_fetch.apply this, query.not
    else
      []
        
  fetch: (query) ->
    @_fetch @optimize_query(query)

  find: (query) ->
    _.map @fetch(query), (result) => @item_set[result]

module.exports =
  QueryError: QueryError
  Store: Store
