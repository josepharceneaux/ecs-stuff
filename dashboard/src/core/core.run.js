(function () {
    'use strict';

    angular.module('app.core')
        .run(runFunction);

    // ----- runFunction -----
    runFunction.$inject = ['$rootScope', '$state', '$cookies', 'OAuth'];

    /* @ngInject */
    function runFunction($rootScope, $state, $cookies, OAuth) {
        $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
            toState.data = toState.data || {};
            toState.data.demoMode = $cookies.get('demoMode') === 'true';

            if (toState.redirectTo) {
                event.preventDefault();
                $state.go(toState.redirectTo, toParams);
                return;
            }

            // If already authenticated, redirects to the last page or dashboard page
            if (toState.data.nonAuthOnly && OAuth.isAuthenticated()) {
                event.preventDefault();
                if (angular.isDefined($rootScope.redirectTo)) {
                    $state.go($rootScope.redirectTo.state, $rootScope.redirectTo.params);
                } else {
                    $state.go('dashboard');
                }
            } else {
                $rootScope.redirectTo = {
                    state: toState,
                    params: toParams
                };

                // If the user is not authenticated and tries to browse the pages restricted
                if (angular.isDefined(toState.data.loginRequired) && toState.data.loginRequired) {
                    if (!OAuth.isAuthenticated()) {
                        $state.go('login', {errorMessage: 'Please log in!'});

                        event.preventDefault();
                    }
                }
            }
        });

        $rootScope.$on('$stateChangeError', function (event, toState, toParams, fromState, fromParams, error) {
            // TODO: handle state change errors caused by failure to resolve dependencies
            // possible reasons for failure:
            //   1) timeout or server failure,
            //   2) user's access token AND refresh token have expired

            event.preventDefault();
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
