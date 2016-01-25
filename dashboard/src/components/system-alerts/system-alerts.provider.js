(function () {
    'use strict';

    angular
        .module('app.systemAlerts')
        .provider('systemAlertsService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['alertService'];

        /* @ngInject */
        function $get(alertService) {

            var alerts;

            return {
                getAlerts: getAlerts,
                createAlert: createAlert
            };

            function getAlerts() {
                // Always return alerts, and preserve its reference to the original object,
                // so anywhere that has already requested alerts will get any updates.
                // IF this service needs to be consumed outside the system alerts module
                // (i.e. by multiple different sources), then we can look at creating a
                // subscription service so instead each services then gets its own, unlinked
                // set of alerts and will be free to manipulate the alerts without affecting
                // other services also requesting alerts. A service may choose to  publish
                // changes and/or listen for published updates (e.g. new incoming alerts,
                // alert status updates (read/unread)), if they choose.

                var request = alertService.all('system-alerts').getList();
                alerts = alerts || request.$object;
                request.then(updateAlerts);
                return alerts;
            }

            function updateAlerts(newAlerts) {
                if (alerts !== newAlerts) {
                    angular.extend(alerts, newAlerts);
                }
            }

            function createAlert(message) {
                alerts.push({
                    date_created: new Date().toISOString(),
                    message: message
                });
            }
        }
    }

})();
