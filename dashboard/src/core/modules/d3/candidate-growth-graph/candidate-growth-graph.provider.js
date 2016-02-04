(function () {
    'use strict';

    angular
        .module('app.core')
        .provider('candidateGrowthService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['$q', 'candidatePoolService'];

        /* @ngInject */
        function $get($q, candidatePoolService) {

            return {
                getPipelineStats: getPipelineStats
            };

            /*
             * @required params
             * @required params.from_date
             * @optional params.to_date; default = current date
             * @optional params.interval; default = 1
             */
            function getPipelineStats(pipelineId, params) {
                var abort = $q.defer();
                var httpConfig = {
                    timeout: abort.promise
                };
                var request;

                if (!angular.isDefined(params)) {
                    throw new TypeError("Invalid argument: `params` must be defined.");
                } else if (!angular.isObject(params)) {
                    throw new TypeError("Invalid argument: `params` must be an `Object`.");
                }

                if (!angular.isDefined(params.from_date)) {
                    throw new TypeError("Invalid argument: `params.from_date` must be defined.");
                } else if (angular.isDate(params.from_date)) {
                    params.from_date = params.from_date.toISOString();
                }

                if (!angular.isDefined(params.to_date)) {
                    params.to_date = new Date().toISOString();
                } else if (angular.isDate(params.to_date)) {
                    params.to_date = params.to_date.toISOString();
                }

                params.interval = params.interval || 1;

                request = candidatePoolService.one('talent-pipeline', pipelineId).withHttpConfig(httpConfig).customGETLIST('stats', params);
                request.cancel = function () {
                    abort.resolve();
                };
                return request;
            }
        }
    }

})();
