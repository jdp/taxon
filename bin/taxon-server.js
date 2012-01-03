#!/usr/bin/env node

var crypto = require('crypto')
  , http = require('http')
  , winston = require('winston')
  , taxondb = require('../');

var store = new taxondb.Store()
  , logger = new (winston.Logger)({
  transports: [
    new (winston.transports.Console)({
      colorize:  true,
      timestamp: true
    })
  ]
});

var server = new taxondb.Server(store, logger)
server.start(8980)
