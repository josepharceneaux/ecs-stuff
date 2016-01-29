(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolsDashboardTeams', directiveFunction)
        .controller('TalentPoolsDashboardTeamsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pools-dashboard-teams/talent-pools-dashboard-teams.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolsDashboardTeamsController',
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
            logger.log('Activated Talent Pools Dashboard Teams View');
        }

        function init() {
            //
        }
    }
})();
