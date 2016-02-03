(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('resumeService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'resumeServiceInfo'];

        /* @ngInject */
        function $get(baseService, resumeServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(resumeServiceInfo.THE_REAL_baseUrl);
            });
        }
    }

})();
