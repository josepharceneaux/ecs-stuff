(function () {
    'use strict';

    angular.module('app.onboard')
        .directive('gtOnboardOrganize', directiveFunction)
        .controller('OnboardOrganizeController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/onboard/onboard-organize/onboard-organize.html',
            replace: true,
            scope: {},
            controller: 'OnboardOrganizeController',
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
            logger.log('Activated Onboard Organize View');
        }
    }
})();
