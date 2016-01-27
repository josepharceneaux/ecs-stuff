(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('socialNetworkService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'socialNetworkServiceInfo'];

        /* @ngInject */
        function $get(baseService, socialNetworkServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(socialNetworkServiceInfo.baseUrl);
            });
        }
    }

})();
