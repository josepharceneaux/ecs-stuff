/*jshint node:true*/
'use strict';

var express = require('express');
var cors = require('cors');
var app = express();
var bodyParser = require('body-parser');
var favicon = require('serve-favicon');
var port = process.env.PORT || 4000;
var four0four = require('./utils/404')();

app.use(cors({origin: true}));

var environment = process.env.NODE_ENV;

app.use(favicon(__dirname + '/icon.png'));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

if(typeof(process.env.ENV) == "undefined"){
  process.env.ENV = 'development';
}

app.use('/api', require('./routes'));

console.log('About to crank up node');
console.log('PORT=' + port);
console.log('NODE_ENV=' + process.env.ENV);

switch (environment) {
  case 'build':
    console.log('** BUILD **');
    app.use(express.static('./build/'));
    // Any invalid calls for templateUrls are under app/* and should return 404
    app.use('/app/*', function(req, res, next) {
      four0four.send404(req, res);
    });
    // Any deep link calls should return index.html
    app.use('/*', express.static('./build/index.html'));
    break;
  default:
    console.log('** DEV **');
    app.use(express.static('./src/client/'));
    app.use(express.static('./'));
    app.use(express.static('./.tmp'));
    // Any invalid calls for templateUrls are under app/* and should return 404
    app.use('/app/*', function(req, res, next) {
      four0four.send404(req, res);
    });
    // Any deep link calls should return index.html
    app.use('/*', express.static('./src/client/index.html'));
    break;
}

app.listen(port, function() {
  console.log('Express server listening on port ' + port);
  console.log('env = ' + app.get('env') +
    '\n__dirname = ' + __dirname +
    '\nprocess.cwd = ' + process.cwd());
});
