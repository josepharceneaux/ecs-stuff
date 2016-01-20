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
                RestangularConfigurer
                    .setBaseUrl(candidateServiceInfo.baseUrl)
                    .addResponseInterceptor(function (data, operation, what, url, response, deferred) {
                        // keep this here as a reference: we shouldn't need to map any requests.
                        // If you think you're requesting a list, but the response returns more
                        // than a list (i.e. the response is an object) and one of the properties
                        // is an array, but it includes other properties, such as total_items. Then
                        // a customGET should be used and the list can be extracted or handled in
                        // some service between this and the consuming view controller. It's likely
                        // that the view controller will want to make use of that other information,
                        // e.g. display the total_items in the view. But if not, again, the list can be
                        // extracted in a service between this and the controller.

                        // DON'T do
                        //var mappings = {
                        //    'candidates/search': 'candidates'
                        //};
                        //
                        //if (operation === 'getList' && what in mappings) {
                        //    return data[mappings[what]];
                        //}

                        return data;
                    });
            });
        }
    }

})();
