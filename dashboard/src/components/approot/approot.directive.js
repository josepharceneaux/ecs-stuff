(function () {

    'use strict';

    angular.module('app.approot')
        .directive('gtApproot', directiveFunction);


    // ----- directiveFunction -----
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/approot/approot.html',
            replace: true,
            scope: {
            }
        };

        return directive;
    }

})();
