(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelineSettings', directiveFunction)
        .controller('PipelineSettingsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipeline-settings/pipeline-settings.html',
            replace: true,
            scope: {},
            controller: 'PipelineSettingsController',
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
            logger.log('Activated Pipeline Settings View');
        }

        function init() {
            //
        }
    }
})();
