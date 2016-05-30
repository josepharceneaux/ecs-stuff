(function() {
  'use strict';

  angular
    .module('app.core')
    .factory('api_info', apiInfo);

  apiInfo.$inject = ['$http'];
  /* @ngInject */
  function apiInfo($http) {
    var service = {
      read_apiInfo: read_apiInfo
    };

    return service;

    function read_apiInfo() {
      $http.get('/api/api-config')
        .then(function (response) {
          service["apiInfo"] = response.data.apiInfo;
        })
        .catch(function (err) {
          /* Ignore */
        });
    }
  }
})();

