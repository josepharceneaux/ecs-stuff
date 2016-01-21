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

            function getCandidates() {
                console.log('fetching candidates');
                return candidateService.all('candidates/search').customGET().then(function (response) {
                    return response.candidates;
                });
            }
        }
    }

})();
