(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('activityService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'activityServiceInfo'];

        /* @ngInject */
        function $get(baseService, activityServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(activityServiceInfo.baseUrl);
            });
        }
    }

})();
