/**
 * Created by Saad Abdullah on 5/16/16.
 */

/**
 * UserToken manages cookies and saves bearer token sent by auth service. So, that token can be used to send request
 * to other services
 */
(function () {
  'use strict';

  angular
    .module('app.components')
    .factory('UserToken', UserToken);
  /* @ngInject */
  function UserToken($cookies, $rootScope, $http, apiInfo, $state, $q) {

    function error() {
      $rootScope.$broadcast('loggedIn', false);
      $state.go('login');
    }

    var service = {
      userId: '',
      accessToken: '',
      goToLogin: goToLogin,
      isLoggedIn: function () {
        var deferred = $q.defer();

        $http({
          method: 'GET',
          url: apiInfo.apiInfo.authService.authorizePath,
          headers: {
            'Authorization': 'Bearer ' + $cookies.get('token'),
            'Content-Type': 'application/json'
          }
        })
          .then(function (response) {
            if ('user_id' in response.data) {
              service.accessToken = $cookies.get('token');
              $rootScope.$broadcast('loggedIn', true);
              deferred.resolve(true);
            }
            else{
              deferred.resolve(false);
            }
          }, function (err) {
            deferred.resolve(false);
          });
        return deferred.promise;
      },
      logout: function () {
        $cookies.remove('token');
        $rootScope.$broadcast('loggedIn', false);
      },
      /**
       * Add cookie of oauth token
       * @param tokenObj:
       */
      authenticate: function (tokenObj) {

        this.accessToken = tokenObj['access_token'];
        var expiry = moment(tokenObj['expires_in'], 'Wdy, DD Mon YYYY HH:MM:SS GMT').format();
        $cookies.put('token', this.accessToken, {expires: expiry});
        $rootScope.$broadcast('loggedIn', true);
      },

      /**
       * Test if user has rights to access admin panel
       * @param userId
       * @param token
       * @returns {*}
       */
      testAuthenticateUserRole: function (userId, token) {
        var url = apiInfo.apiInfo.userService.baseUrl.concat(userId, apiInfo.apiInfo.userService.userRolesPath);
        return $http({
          method: 'GET',
          url: url,
          params: {
            role_id_only: false
          },
          headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
          }
        });
      },
      login: login
    };
    return service;

    /**
     * Go to login state if user is not authenticated
     * @param $state: state object
     */
    function goToLogin() {
       var deferred = $q.defer();
      service.isLoggedIn().then(function (response) {
        if(!response)
              error();
          return deferred.resolve(response);
      });
      return deferred.promise;
    }

    /**
     *Send request to get-talent auth service and then check if user is authenticated
     * @param email: email string
     * @param password: password string
     * @returns {*|{get}}
     */
    function login(email, password) {
      return $http({
        method: 'POST',
        url: apiInfo.apiInfo.authService.grantPath,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        data: $.param({
          username: email,
          password: password,
          grant_type: 'password',
          client_id: apiInfo.apiInfo.authService.clientId,
          client_secret: apiInfo.apiInfo.authService.clientSecret
        })
      });
    }
  }
})();
