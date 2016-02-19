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


        $get.$inject = ['$q', 'candidatePoolService', 'userService', 'candidateService'];

        /* @ngInject */
        function $get($q, candidatePoolService, userService, candidateService) {
            var candidatePoolService = candidatePoolService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-2ec1c-gettalentcandidatepoolservice.apiary-mock.com/v1');
            });

            var userService = userService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-caacc-gettalentuserservice.apiary-mock.com/v1/');
            });

            function getPipelineDetail(pipelineId) {
                console.log('fetching pipeline detail');
                return candidatePoolService.one('talent-pipelines', pipelineId).customGET().then(
                    function (response) {
                        var user_request = getUserName(response.user_id).then(
                            function (userResponse) {
                                response.user_name = userResponse;
                            });
                    return $q.when(user_request).then(function () {
                        return response;
                    });
                });
            }

            function getUserName(pipelineOwnerId) {
                return userService.one('users', pipelineOwnerId).customGET().then(
                    function (userResponse) {
                        return userResponse.user.first_name + ' ' + userResponse.user.last_name;
                    }
                )
            }

            function getPipelineCandidatesCount(pipelineId) {
                console.log('fetching candidate count');
                return candidatePoolService.one('talent-pipelines', pipelineId)
                    .customGET('candidates', {fields: 'count_only'}).then(
                        function (countResponse) {
                            return countResponse.total_found;
                        }
                    )
            }

            function getPipelineSmartlistsCount(pipelineId) {
                console.log('fetching smartlist count');
                return candidatePoolService.one('talent-pipelines', pipelineId).customGET('smartlists').then(
                    function (smartListResponse) {
                        return smartListResponse.smartlists.length;
                    }
                )
            }

            function getPipelineCandidateInfo(searchParamsObj) {
                console.log('fetching candidate info');
                //Below should have the params in the customGET but using staging data for now
                return candidateService.one('candidates/search').customGET('').then(
                    function (searchResponse) {
                        return searchResponse;
                    })
            }

            return {
                getPipelineDetail: getPipelineDetail,
                getPipelineCandidatesCount: getPipelineCandidatesCount,
                getPipelineSmartlistsCount: getPipelineSmartlistsCount,
                getPipelineCandidateInfo: getPipelineCandidateInfo
            };

        }
    }

})();