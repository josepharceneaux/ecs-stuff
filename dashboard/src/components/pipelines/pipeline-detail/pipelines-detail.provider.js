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


        $get.$inject = ['$q', 'candidatePoolService', 'userService'];

        /* @ngInject */
        function $get($q, candidatePoolService, userService) {
            var candidatePoolService = candidatePoolService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-2ec1c-candidatepoolservice.apiary-mock.com/v1/');
            });

            var userService = userService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-caacc-userservice17.apiary-mock.com/v1/');
            });

            function getPipelineDetail() {
                console.log('fetching pipeline detail');
                return candidatePoolService.one('talent-pipelines', 1).customGET().then(function (response) {
                    var user_request = getUserName().then(function (userResponse) {
                        response.user_name = userResponse;
                    });
                    return $q.when(user_request).then(function () {
                        return response;
                    });
                });
            }

            function getUserName() {
                return userService.one('users', 99).customGET().then(
                    function (userResponse) {
                        return userResponse.user.first_name + ' ' + userResponse.user.last_name;
                    }
                )
            }

            function getPipelineCandidatesCount() {
                console.log('fetching candidate count');
                return candidatePoolService.one('talent-pipeline', 1).customGET('candidates', {fields: 'count_only'}).then(
                    function (countResponse) {
                        return countResponse.total_found;
                    }
                )
            }

            function getPipelineSmartlistsCount() {
                console.log('fetching smartlist count');
                return candidatePoolService.one('talent-pipeline', 1).customGET('smart_lists').then(
                    function (smartListResponse) {
                        return smartListResponse.smart_lists.length;
                    }
                )
            }

            return {
                getPipelineDetail: getPipelineDetail,
                getPipelineCandidatesCount: getPipelineCandidatesCount,
                getPipelineSmartlistsCount: getPipelineSmartlistsCount
            };

        }
    }

})();