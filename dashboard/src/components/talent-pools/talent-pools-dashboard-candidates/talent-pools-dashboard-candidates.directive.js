(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolsDashboardCandidates', directiveFunction)
        .controller('TalentPoolsDashboardCandidatesController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pools-dashboard-candidates/talent-pools-dashboard-candidates.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolsDashboardCandidatesController',
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
            logger.log('Activated Talent Pools Dashboard Candidates View');
        }

        function init() {
            //
        }
    }
})();
