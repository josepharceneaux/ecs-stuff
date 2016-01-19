(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidateService', providerFunction)

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['gtRestangular', 'candidateServiceInfo'];

        /* @ngInject */
        function $get(gtRestangular, candidateServiceInfo) {
            return gtRestangular.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl(candidateServiceInfo.baseUrl);
                RestangularConfigurer.addResponseInterceptor(function (data, operation, what, url, response, deferred) {
                    var mappings = {
                        'candidates': 'candidates'
                    };

                    if (operation === 'getList' && what in mappings) {
                        return data[mappings[what]];
                    }
                    return data;
                });
            });
        }
    }

})();
