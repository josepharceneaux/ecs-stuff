(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('emailCampaignService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['baseService', 'emailCampaignServiceInfo'];

        /* @ngInject */
        function $get(baseService, emailCampaignServiceInfo) {
            return baseService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(emailCampaignServiceInfo.baseUrl);
            });
        }
    }

})();
