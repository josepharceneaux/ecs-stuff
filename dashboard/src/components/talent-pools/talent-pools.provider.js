(function () {
    'use strict';

    angular
        .module('app.systemAlerts')
        .provider('talentPoolsService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['candidatePoolService'];

        /* @ngInject */
        function $get(candidatePoolService) {
            var talentPoolsService = candidatePoolService.withConfig(function (RestangularConfigurer) {
            });

            return {
                createTalentPools: createTalentPools
            };

            function createTalentPools(talentPools) {
                return talentPoolsService.all('talent-pools').post(talentPools);
            }
        }
    }

})();
