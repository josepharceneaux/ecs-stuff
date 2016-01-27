(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidateService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'candidateServiceInfo'];

        /* @ngInject */
        function $get(baseService, candidateServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer
                    .setBaseUrl(candidateServiceInfo.baseUrl);
            });
        }
    }

})();
