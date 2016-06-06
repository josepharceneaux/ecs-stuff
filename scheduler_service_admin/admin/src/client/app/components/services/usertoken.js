/**
 * Created by Saad Abdullah on 5/16/16.
 */

(function() {
  'use strict';

  angular
    .module('app.components')
    .factory('UserToken', UserToken);
  /* @ngInject */
  function UserToken($cookies, $rootScope, $http, api_info, $state) {

    function error(){
       $rootScope.$broadcast('loggedIn', false);
       $state.go('login');
    }

    var service = {
      user_id: '',
      access_token: '',
      goToLogin: goToLogin,
      is_logged_in: function () {
        return $http({
            method: 'GET',
            url: api_info.apiInfo.authService.authorizePath,
            headers: {
            'Authorization': 'Bearer ' + $cookies.get('token'),
                'Content-Type': 'application/json'
              }
          })
          .then(function (response) {
              if("user_id" in response.data){
                 service.access_token = $cookies.get('token');
                $rootScope.$broadcast('loggedIn', true);
                return;
              }
            error();
            }, function (err) {
                error();
          });
      },
      logout_user: function () {
        $cookies.remove('token');
        $rootScope.$broadcast('loggedIn', false);
      },
      authenticate_user: function (token_obj) {

        this.access_token = token_obj['access_token'];
        var expiry = moment(token_obj['expires_in'], "Wdy, DD Mon YYYY HH:MM:SS GMT").format();
        $cookies.put('token',this.access_token,{expires: expiry});
        $rootScope.$broadcast('loggedIn', true);
      },

      /**
       * Test if user has rights to access admin panel
       * @param user_id
       * @param token
       * @returns {*}
         */
      test_authenticate_user_role: function (user_id, token) {
        var url = api_info.apiInfo.userService.baseUrl.concat(user_id, api_info.apiInfo.userService.userRolesPath);
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
      login_user: login_user
    };
    return service;

    /**
   * Go to login state if user is not authenticated
   * @param $state: state object
     */
    function goToLogin(){
      return service.is_logged_in();
    }

    /**
     *Send request to get-talent auth service and then check if user is authenticated
     * @param email: email string
     * @param password: password string
     * @returns {*|{get}}
       */
    function login_user(email, password){
      return $http({
         method: 'POST',
         url: api_info.apiInfo.authService.grantPath,
         headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
         },
         data: $.param({
           username: email,
           password: password,
           grant_type: "password",
           client_id: api_info.apiInfo.authService.clientId,
           client_secret: api_info.apiInfo.authService.clientSecret
         })
       });
    }
  }
})();
