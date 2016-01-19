(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('userService', providerFunction)

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['gtRestangular', 'userServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, userServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(userServiceInfo.baseUrl);
            });
        }
    }

})();
