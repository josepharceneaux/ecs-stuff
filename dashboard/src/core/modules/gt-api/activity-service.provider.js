(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('activityService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['gtRestangular', 'activityServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, activityServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(activityServiceInfo.baseUrl);
            });
        }
    }

})();
