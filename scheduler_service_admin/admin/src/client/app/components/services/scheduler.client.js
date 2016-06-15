/**
 * Scheduler Client service gets the tasks using filters from scheduler service
 */
(function () {
  'use strict';

  angular
    .module('app.core')
    .factory('SchedulerClientService', schedulerDataService);

  schedulerDataService.$inject = ['$http', 'exception', 'UserToken', 'apiInfo', '$q'];
  /* @ngInject */
  function schedulerDataService($http, exception, UserToken, apiInfo, $q) {
    var service = {
      getTasks: getTasks
    };

    return service;

    /**
     * Get tasks based on param filters
     * @param filters (type:object) paused, task_type, task_category, userId
     * @returns {*|promise}
       */
    function getTasks(filters) {
      var deferred = $q.defer();
      $http(
        {
          url: apiInfo.apiInfo.schedulerServiceAdmin.taskUrl,
          method: 'GET',
          params: filters,
          headers: {
            'Authorization': 'Bearer ' + UserToken.accessToken,
            'Content-Type': 'application/json'
          }
        })
        .then(success, fail);

      return deferred.promise;

      function success(response) {
        return deferred.resolve({data: response.data, headers: response.headers});
      }

      function fail(e) {
        return deferred.resolve(exception.catcher('XHR Failed for getTasks')(e));
      }
    }
  }
})();
