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
                RestangularConfigurer.setBaseUrl('https://private-120a6-candidatepoolservice.apiary-mock.com/v1');
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
