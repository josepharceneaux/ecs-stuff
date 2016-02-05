(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidatePoolService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'candidatePoolServiceInfo'];

        /* @ngInject */
        function $get(baseService, candidatePoolServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(candidatePoolServiceInfo.baseUrl);
            });
        }
    }

})();
