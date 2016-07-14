/**
 * API info service reads the URLs from node server and saves them in a dictionary. So, that other services and controllers
 * can use these URLs to call auth service, scheduler service and user service
 */
(function () {
  'use strict';

  angular
    .module('app.core')
    .factory('apiInfo', apiInfo);

  apiInfo.$inject = ['$http', '$q'];
  /* @ngInject */
  function apiInfo($http, $q) {
    var service = {
      readApiInfo: readApiInfo
    };

    return service;

    /**
     * Read apiInfo from node server containing URLs of talent flask services of dev, staging and prod environment
     * @returns {*|promise}
       */
    function readApiInfo() {

      var deferred = $q.defer();
      $http.get('/api/api-config')
        .then(function (response) {
          service['apiInfo'] = response.data.apiInfo;
          return deferred.resolve(service);
        })
        .catch(function (err) {
          /* Ignore */
          return deferred.reject('Error Occurred');
        });

      return deferred.promise;
    }
  }
})();
