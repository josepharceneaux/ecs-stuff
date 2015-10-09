(function() {
    'use strict';

    angular.module('app.core')
        .run(runFunction);

    // ----- runFunction -----
    runFunction.$inject = ['$rootScope', '$state'];

    /* @ngInject */
    function runFunction($rootScope, $state) {
        $rootScope.$on('$stateChangeStart', function(evt, to, params) {
            if (to.redirectTo) {
                evt.preventDefault();
                $state.go(to.redirectTo, params);
            }
        })
    }
})();