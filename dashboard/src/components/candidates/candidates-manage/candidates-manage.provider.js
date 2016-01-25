(function () {
    'use strict';

    angular
        .module('app.candidates')
        .provider('candidatesManageService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['candidateService'];

        /* @ngInject */
        function $get(candidateService) {
            return {
                getCandidates: getCandidates
            };

            function getCandidates(params) {
                console.log('fetching candidates');
                params = params || {};
                return candidateService.all('candidates').customGET('search', params).then(function (response) {
                    return response;
                });
            }
        }
    }

})();
