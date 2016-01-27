(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('smsCampaignService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'smsCampaignServiceInfo'];

        /* @ngInject */
        function $get(baseService, smsCampaignServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(smsCampaignServiceInfo.baseUrl);
            });
        }
    }

})();
