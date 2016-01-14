(function () {
    'use strict';

    angular
        .module('app.pipelines')
        .directive('gtPipelines', directiveFunction)
        .controller('PipelinesController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipelines.html',
            replace: true,
            scope: {},
            controller: 'PipelinesController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated Pipelines View');
        }
    }
})();
