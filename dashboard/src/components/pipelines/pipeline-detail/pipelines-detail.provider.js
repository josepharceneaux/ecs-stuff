(function () {
    'use strict';

    angular
        .module('app.pipelines')
        .provider('pipelinesDetailService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;


        $get.$inject = ['candidatePoolService'];

        /* @ngInject */
        function $get(candidatePoolService) {
            var tempService = candidatePoolService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-2ec1c-candidatepoolservice.apiary-mock.com/v1/');
            });

            function getPipelineDetail() {
                console.log('fetching pipeline detail');
                //return tempService.all('talent-pipelines').customGET().then(function (response) {
                //
                //});
            }

            return {
                getPipelineDetail: getPipelineDetail
            };

        }
    }

})();