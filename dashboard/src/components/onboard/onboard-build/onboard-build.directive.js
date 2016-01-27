(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardBuild', directiveFunction)
        .controller('OnboardBuildController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-build/onboard-build.html',
            replace: true,
            scope: {},
            controller: 'OnboardBuildController',
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
            logger.log('Activated Onboard Build View');
        }

        function init() {
            //
        }
    }
})();
