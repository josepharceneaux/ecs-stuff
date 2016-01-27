(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('smartlistService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'smartlistServiceInfo'];

        /* @ngInject */
        function $get(baseService, smartlistServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(smartlistServiceInfo.baseUrl);
            });
        }
    }

})();
