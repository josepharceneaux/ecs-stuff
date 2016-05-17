var router = require('express').Router();
var four0four = require('./utils/404')();
var data = require('./data');

router.get('/login', login_user);
router.get('/*', four0four.notFoundMiddleware);

module.exports = router;

//////////////

function login_user(req, res, next) {
  res.status(200).send(data.people);
}
