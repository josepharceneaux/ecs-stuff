(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelineTeam', directiveFunction)
        .controller('PipelineTeamController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipeline-team/pipeline-team.html',
            replace: true,
            scope: {
            },
            controller: 'PipelineTeamController',
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
            logger.log('Activated Pipeline Team View');
        }

        function init() {
            //
        }
    }
})();
