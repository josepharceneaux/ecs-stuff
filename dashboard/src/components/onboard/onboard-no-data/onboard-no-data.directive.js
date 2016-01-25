(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardNoData', directiveFunction)
        .controller('OnboardNoDataController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-no-data/onboard-no-data.html',
            replace: true,
            scope: {},
            controller: 'OnboardNoDataController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {

        activate();

        function activate() {
            logger.log('Activated Onboard No Data View');
        }
    }
})();
