(function () {
    'use strict';

    angular.module('app.core')
        .run(runFunction);

    // ----- runFunction -----
    runFunction.$inject = ['$rootScope', '$state', '$cookies', 'OAuth'];

    /* @ngInject */
    function runFunction($rootScope, $state, $cookies, OAuth) {
        $rootScope.$on('$stateChangeStart', function (evt, to, params) {
            to.data = to.data || {};
            to.data.demoMode = $cookies.get('demoMode') === 'true';

            if (to.redirectTo) {
                evt.preventDefault();
                $state.go(to.redirectTo, params);
                return;
            }

            if (to.name === 'login') {
                // If already authenticated, redirects to the last page or dashboard page
                if (OAuth.isAuthenticated()) {
                    if (angular.isDefined($rootScope.redirectTo)) {
                        $state.go($rootScope.redirectTo.state, $rootScope.redirectTo.params);
                    } else {
                        $state.go('dashboard');
                    }
                }
            } else {
                $rootScope.redirectTo = {
                    state: to,
                    params: params
                };

                // If the user is not authenticated and tries to browse the pages restricted
                if (angular.isDefined(to.data) && angular.isDefined(to.data.loginRequired) && to.data.loginRequired) {
                    if (!OAuth.isAuthenticated()) {
                        $state.go('login', {errorMessage: 'Please log in!'});

                        evt.preventDefault();
                    }
                }
            }
        });

        $rootScope.$on('oauth:error', function (event, rejection) {
            // Ignore `invalid_grant` error - should be catched on `LoginController`.
            if ('invalid_grant' === rejection.data.error) {
                return;
            }

            // Refresh token when a `invalid_token` error occurs.
            if ('invalid_token' === rejection.data.error) {
                return OAuth.getRefreshToken();
            }

            // Redirect to `/login` with the `error_reason`.
            $state.to('login', {errorMessage: rejection.data.error});
        });
    }
})();
