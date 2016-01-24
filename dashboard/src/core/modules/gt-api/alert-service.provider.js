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

        $get.$inject = ['gtRestangular', 'alertServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, alertServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(alertServiceInfo.baseUrl);
            });
        }
    }

})();
