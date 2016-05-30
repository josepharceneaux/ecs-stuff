(function() {
  'use strict';

  angular
    .module('app.core')
    .factory('SchedulerClientService', scheduler_dataservice);

  scheduler_dataservice.$inject = ['$http', '$q', 'exception', 'logger', 'UserToken', 'api_info'];
  /* @ngInject */
  function scheduler_dataservice($http, $q, exception, logger, UserToken, api_info) {
    var service = {
      getTasks: getTasks,
      getMessageCount: getMessageCount
    };

    return service;

    function getMessageCount() { return $q.when(72); }

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
        //.then(success)
        .success(function(data, headers, config){
          console.log('Response', data, headers, config);
        })
        .catch(fail);

      function success(response) {
        console.log(response.headers('X-Page'));
        return {data: response.data, headers: response.headers};
      }

      function fail(e) {
        return exception.catcher('XHR Failed for getPeople')(e);
      }
    }
  }
})();
