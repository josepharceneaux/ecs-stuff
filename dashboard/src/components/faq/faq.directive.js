(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtFaq', directiveFunction)
        .controller('FaqController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/faq/faq.html',
            replace: true,
            scope: {},
            controller: 'FaqController',
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
