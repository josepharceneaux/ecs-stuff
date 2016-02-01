(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('userService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'userServiceInfo'];

        /* @ngInject */
        function $get(baseService, userServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(userServiceInfo.baseUrl);
            });
        }
    }

})();
