(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolCreate', directiveFunction)
        .controller('TalentPoolCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pool-create/talent-pool-create.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolCreateController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'logger', 'systemAlertsService', 'talentPoolsService'];

    /* @ngInject */
    function ControllerFunction($state, logger, systemAlertsService, talentPoolsService) {
        var vm = this;

        vm.createTalentPool = createTalentPool;

        init();
        activate();

        function activate() {
            logger.log('Activated Talent Pool Create View');
        }

        function init() {
            //
        }

        function createTalentPool(talentPool) {
            var talentPools = [
                talentPool
            ];
            talentPoolsService.createTalentPools(talentPools).then(function (response) {
                var poolId = response.talent_pools[0];
                if (poolId) {
                    systemAlertsService.createAlert('Talent pool <strong>"$poolName"</strong> successfully created.'.replace('$poolName', talentPool.name));
                    $state.go('talentPools.talentPool', { poolId: poolId })
                }
            });
        }
    }
})();
