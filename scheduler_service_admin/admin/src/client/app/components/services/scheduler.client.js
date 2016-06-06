(function() {
  'use strict';

  angular
    .module('app.core')
    .factory('SchedulerClientService', scheduler_dataservice);

  scheduler_dataservice.$inject = ['$http', 'exception', 'UserToken', 'api_info'];
  /* @ngInject */
  function scheduler_dataservice($http, exception,UserToken, api_info) {
    var service = {
      getTasks: getTasks
    };

    return service;

    function getTasks(filters) {
      return $http(
        {
          url: api_info.apiInfo.schedulerServiceAdmin.taskUrl,
          method: 'GET',
          params: filters,
          headers: {
            'Authorization': 'Bearer ' + UserToken.access_token,
            'Content-Type': 'application/json'
          }
        })
        .then(success)
        .catch(fail);

      function success(response) {
        return {data: response.data, headers: response.headers};
      }

      function fail(e) {
        return exception.catcher('XHR Failed for getTasks')(e);
      }
    }
  }
})();
