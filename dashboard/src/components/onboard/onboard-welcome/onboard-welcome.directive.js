(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardWelcome', directiveFunction)
        .controller('OnboardWelcomeController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-welcome/onboard-welcome.html',
            replace: true,
            scope: {},
            controller: 'OnboardWelcomeController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger', '$mdDialog'];

    /* @ngInject */
    function ControllerFunction(logger, $mdDialog) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Onboard Welcome View');
        }

        function init() {
            //
        }
    }
})();
