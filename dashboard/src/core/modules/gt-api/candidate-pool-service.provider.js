(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidatePoolService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['gtRestangular', 'candidatePoolServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, candidatePoolServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(candidatePoolServiceInfo.baseUrl);
            });
        }
    }

})();
