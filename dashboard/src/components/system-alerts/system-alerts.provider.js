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

        $get.$inject = ['userService'];

        /* @ngInject */
        function $get(userService) {
            // TODO: replace with appropriate service and endpoint once a system alerts api has been developed
            var alertsService = userService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('http://localhost:7203/api');
            });

            return {
                getAlerts: getAlerts
            };

            function getAlerts() {
                return alertsService.all('system-alerts').customGET().then(function (response) {
                    return response;
                });
            }
        }
    }

})();
