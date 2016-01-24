(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidateService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['gtRestangular', 'candidateServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, candidateServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer
                    .setBaseUrl(candidateServiceInfo.baseUrl);
            });
        }
    }

})();
