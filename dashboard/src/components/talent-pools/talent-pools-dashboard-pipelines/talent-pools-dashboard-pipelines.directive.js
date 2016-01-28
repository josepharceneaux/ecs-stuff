(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolsDashboardPipelines', directiveFunction)
        .controller('TalentPoolsDashboardPipelinesController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pools-dashboard-pipelines/talent-pools-dashboard-pipelines.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolsDashboardPipelinesController',
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
            logger.log('Activated Talent Pools Dashboard Pipelines View');
        }

        function init() {
            //
        }
    }
})();
