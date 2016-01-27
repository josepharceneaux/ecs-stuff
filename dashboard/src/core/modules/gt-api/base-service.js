(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('baseService', providerFunction);

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
                    .addResponseInterceptor(function (data, operation, what, url, response, deferred) {
                        var extractedData = [];

                        if (operation === 'getList' && !angular.isArray(data)) {
                            // When requesting a list of resources, it's reasonable to expect
                            // that only one property in an API's JSON response ought to
                            // be a list. The rest should be single value properties or objects.
                            // If it turns out later on that one of our API's does return multiple
                            // list properties on the top level of a response object, move
                            // this down a level or two as necessary.

                            Object.keys(data).forEach(function (key) {
                                if (angular.isArray(data[key])) {
                                    data[key].forEach(function (item) {
                                        extractedData.push(item);
                                    });
                                } else {
                                    extractedData[key] = data[key];
                                }
                            });
                            return extractedData;
                        }

                        return data;
                    })
                    .setErrorInterceptor(function (response, deferred, responseHandler) {
                        if (response.status === 401) {
                            OAuth.getRefreshToken().then(function () {
                                $http(response.config).then(responseHandler, deferred.reject);
                            }, function () {
                                throw new Error('Unable to renew your session. Please log out and back in again');
                            });

                            return false; // error handled
                        }
                         return true; // error not handled
                    });
            });
        }
    }

})();
