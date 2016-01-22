(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardGetStarted', directiveFunction)
        .controller('OnboardGetStartedController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-get-started/onboard-get-started.html',
            replace: true,
            scope: {},
            controller: 'OnboardGetStartedController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Onboard Get Started View');
        }

        function init() {
            //
        }
    }
})();
