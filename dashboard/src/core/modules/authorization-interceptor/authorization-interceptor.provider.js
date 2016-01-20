(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('authorizationInterceptor', providerFunction)

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = [];

        /* @ngInject */
        function $get() {
            return {
                request: function (config) {
                    var data;
                    // don't add the authorization header when the client is requesting a new token or refreshing one.
                    // this should override angular-oauth2 adding the stored AuthorizationHeader
                    if (angular.isDefined(config.data)) {
                        data = queryString.parse(config.data);
                        if (angular.isDefined(data.grant_type) && (data.grant_type === 'password' || data.grant_type === 'refresh_token')) {
                            if (angular.isDefined(config.headers.Authorization)) {
                                delete config.headers.Authorization;
                            }
                        }
                    }
                    return config;
                }
            };
        }
    }

})();
