(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('gtRestangular', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['$http', 'Restangular', 'OAuth', 'OAuthToken'];

        /* @ngInject */
        function $get($http, Restangular, OAuth, OAuthToken) {
            return Restangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer
                    .setDefaultHeaders({
                        // OAuth (angular-oauth2) actually already adds this by default via an $http request interceptor
                        Authorization: function () {
                            return OAuthToken.getAuthorizationHeader();
                        }
                    })
                    .setErrorInterceptor(function (response, deferred, responseHandler) {
                        if (response.status === 401) {
                            OAuth.getRefreshToken().then(function () {
                                $http(response.config).then(responseHandler, deferred.reject);
                            });

                            return false; // error handled
                        }
                         return true; // error not handled
                    });
            });
        }
    }

})();
