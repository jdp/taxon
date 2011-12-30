
# TaxonDB

_Note that this is a prototype implemented with NodeJS and CoffeeScript. Actual implementation is likely to change._

TaxonDB is a small data store exposing tagged data over HTTP as JSON that allows arbitrary boolean queries supporting `and`, `or`, and `not` operations on those tags.

## RESTful API

TaxonDB's server exposes its data over HTTP, and by default runs on port 8980. All of the current API is namespaced under the `/v1` path. Two resources are exposed, the tags resource and the items resource, which are available under `/v1/tags` and `/v1/items` respectively.

### Tags Endpoints

#### Fetch All Tags

Endpoint: `GET /v1/tags`

A list of each unique tag is available by making this request. The list is kept up to date during item addition and removal.

Responses:

* `200` OK.

### Items Endpoints

All objects returned in the items endpoints share the same structure. A TaxonDB "item" is an object with three properties: an `_id`, which is used as a unique identifier; `data`, arbitrary string data attached to that item; and `tags`, an array of each tag associated with the item.

    {
      _id:  "probably-a-uuid",
      data: "arbitrary string data",
      tags: ["set", "of", "tags"]
    }

#### Fetch All Items

Endpoint: `GET /v1/items`

With no filters, this will return a blob of ever single item in the database. Queries can be used to filter the result set according to the tag relationships on the items.

Parameters:

* `query` An arbitrary boolean tag query. _(optional)_

Responses:

* `200` OK.
* `400`. Bad Request. Likely because of a malformed query.

#### Fetch Individual Item

Endpoint: `GET /v1/items/:id`

Making a request to this endpoint will return the item with the specified `id`.

Responses:

* `200` OK.
* `404` Not Found.

#### Create an Item

Endpoint: `POST /v1/items`

Creating an item will add it to the index and it will immediately show in subsequent queries.

Parameters:

* `id` The unique identifier of the item. _(required)_
* `data` Arbitrary data associated with the item. _(required)_
* `tag` Tag associated with the data. To add multiple tags, provide multiple `tag` parameters. _(required)_

Responses:

* `201` Created.
* `400` Bad Request. Likely because of a missing required parameter.

_Caveat: The NodeJS query string and form data parser will automatically convert multiple instances of the same field name into an array. This may be uncommon behavior, as it is common in web forms, other web frameworks, and functions like PHP's `http_build_query` to append and use index fields when encoding and reading arrays in query strings and form data. It is likely that the `tag` parameter will become `tags` and tags will be provided in a comma-separated string._
