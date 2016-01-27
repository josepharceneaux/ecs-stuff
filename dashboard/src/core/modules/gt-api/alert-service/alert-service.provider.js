(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('alertService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'alertServiceInfo'];

        /* @ngInject */
        function $get(baseService, alertServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(alertServiceInfo.baseUrl);
            });
        }
    }

})();
