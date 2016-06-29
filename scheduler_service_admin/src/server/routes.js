var router = require('express').Router();
var four0four = require('./utils/404')();
var apiconfig = require('./config.json');
var environment = process.env.ENV;

router.get('/api-config', getconfig);
router.get('/*', four0four.notFoundMiddleware);

module.exports = router;

//////////////

function getconfig(req, res, next) {

  if (environment === 'development') {
    res.status(200).send(apiconfig.local);
  }
  else if (environment === 'stagging') {
    res.status(200).send(apiconfig.development);
  }
  else if (environment === 'production') {

    res.status(200).send(apiconfig.production);
  }
}
