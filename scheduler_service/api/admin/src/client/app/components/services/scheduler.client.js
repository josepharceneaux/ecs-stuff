(function() {
  'use strict';

  var serviceURL = "http://localhost:8011/v1/admin/";
  var getUserTasksURL = serviceURL + "tasks";

  angular
    .module('app.core')
    .factory('SchedulerClientService', scheduler_dataservice);

  scheduler_dataservice.$inject = ['$http', '$q', 'exception', 'logger', 'UserToken'];
  /* @ngInject */
  function scheduler_dataservice($http, $q, exception, logger, UserToken) {
    var service = {
      getTasks: getTasks,
      getMessageCount: getMessageCount
    };

    return service;

    function getMessageCount() { return $q.when(72); }

    function getTasks(filters) {

      return $http.get(getUserTasksURL,
        {
          headers: {
            'Authorization': 'Bearer ' + UserToken.access_token,
            'Content-Type': 'application/json'
          }
        })
        .then(success)
        .catch(fail);

      function success(response) {
        return response.data;
      }

      function fail(e) {
        return exception.catcher('XHR Failed for getPeople')(e);
      }
    }
  }
})();
