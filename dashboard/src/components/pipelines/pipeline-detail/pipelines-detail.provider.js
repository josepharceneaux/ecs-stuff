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
                RestangularConfigurer.setBaseUrl('https://private-2ec1c-candidatepoolservice.apiary-mock.com/v1/');
            });

            var userService = userService.withConfig(function (RestangularConfigurer) {
                RestangularConfigurer.setBaseUrl('https://private-caacc-userservice17.apiary-mock.com/v1/');
            });

            function getPipelineDetail(pipelineId) {
                console.log('fetching pipeline detail');
                return candidatePoolService.one('talent-pipelines', pipelineId).customGET().then(
                    function (response) {
                        var user_request = getUserName(response.owner_user_id).then(
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
                return candidatePoolService.one('talent-pipeline', pipelineId)
                    .customGET('candidates', {fields: 'count_only'}).then(
                        function (countResponse) {
                            return countResponse.total_found;
                        }
                    )
            }

            function getPipelineSmartlistsCount(pipelineId) {
                console.log('fetching smartlist count');
                return candidatePoolService.one('talent-pipeline', pipelineId).customGET('smart_lists').then(
                    function (smartListResponse) {
                        return smartListResponse.smart_lists.length;
                    }
                )
            }

            function getPipelineCandidateInfo(searchParamsObj) {
                console.log('fetching candidate info with: ', searchParamsObj);
                return candidateService.one('candidates/search').customGET('', searchParamsObj).then(
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