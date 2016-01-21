module.exports = function(app) {
    var api = '/api';
    var data = '/../../data/';
    var jsonfileservice = require('./utils/jsonfileservice')();

    app.get(api + '/test-data', getTestData);

    app.get(api + '/system-alerts', getSystemAlerts);

    function getTestData(req, res, next) {
        var json = jsonfileservice.getJsonFromFile(data + 'test-data.json');
        res.send(json);
    }

    function getSystemAlerts(req, res, next) {
        var json = jsonfileservice.getJsonFromFile(data + 'system-alerts.json');
        res.send(json);
    }
};
