(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardEngage', directiveFunction)
        .controller('OnboardEngageController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-engage/onboard-engage.html',
            replace: true,
            scope: {},
            controller: 'OnboardEngageController',
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
            logger.log('Activated Onboard Engage View');
        }
    }
})();
