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

