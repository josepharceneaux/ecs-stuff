(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('gtRestangular', providerFunction)

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['Restangular', 'OAuthToken'];

        /* @ngInject */
        function $get(Restangular, OAuthToken) {
            return Restangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setDefaultHeaders({
                    Authorization: function () {
                        return OAuthToken.getAuthorizationHeader();
                    }
                });
            });
        }
    }

})();
