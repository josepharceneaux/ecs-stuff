(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtSupport', directiveFunction)
        .controller('SupportController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/support/support.html',
            replace: true,
            scope: {},
            controller: 'SupportController',
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
            logger.log('Activated FAQ View');
        }

        function init() {
            //
        }
    }
})();
