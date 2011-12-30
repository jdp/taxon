http = require "http"
journey = require "journey"
queryparser = require "./query_parser"
_ = require "underscore"
uuid = require "uuid"

class Server
  constructor: (store, logger) ->
    @store = store
    @logger = logger
    @router = new journey.Router
    @route()
    @server = http.createServer (request, response) =>
      body = ""
      request.addListener "data", (chunk) ->
        body += chunk
      request.addListener "end", =>
        @router.handle request, body, (result) ->
          result.headers["Server"] = "taxondb/0.0.0"
          result.headers["Connection"] = "close"
          response.writeHead result.status, result.headers
          response.end result.body
          logger.info "#{result.status} #{request.url}"
 
  route: ->
    store = @store

    @router.map ->

      @path "/v1", ->

        # All API endpoints pertaining to tags
        @path "/tags", ->
          @get().bind (req, res) ->
            tags = _.keys(store.tag_set)
            headers =
              "X-Resource-Size": tags.length
            res.send 200, headers, tags

        # All API endpoints pertaining to items
        @path "/items", ->

          # Retrieve or query main item collection
          @get().bind (req, res, params) ->
            headers = {}
            results = []
            if params.query
              query = queryparser.parse(params.query)
              method = if params.shallow then "fetch" else "find"
              try
                results = store[method](query)
              catch e
                throw e if e.name != "QueryError"
                return res.send 400, headers, {error: e.value}
            else
              method = if params.shallow then "keys" else "values"
              results = _[method](store.item_set)
            headers =
              "X-Resource-Size": results.length
            res.send 200, headers, results

          # Add to the item collection
          @post().bind (req, res, params) ->
            return res.send(400, {}, "id parameter missing") unless "id" of params
            return res.send(400, {}, "data parameter missing") unless "data" of params
            return res.send(400, {}, "tags parameter missing") unless "tags" of params

            store.store params.id, JSON.parse(params.data), params.tags
            res.send 201, {}, "ok"

          # Work with individual items
          @path /\/([a-z0-9\-\_]+)/, ->

            @get().bind (req, res, id, params) ->
              if id of store.item_set
                res.send store.item_set[id]
              else
                res.send 404, {}, { error: "item not found" }

  start: (port) ->
    @logger.info "started server on port #{port}"
    @server.listen port

module.exports =
  Server: Server
