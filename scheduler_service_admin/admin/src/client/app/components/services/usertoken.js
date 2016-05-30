/**
 * Created by saad on 5/16/16.
 */

(function() {
  'use strict';

  angular
    .module('app.components')
    .factory('UserToken', UserToken);
  /* @ngInject */
  function UserToken($cookies, $rootScope) {

    var service = {
      access_token: '9ery8pVOxTOvQU0oJsENRek4lj6ZT6',
      refresh_token: '',
      goToLogin: goToLogin,
      is_authenticated_user: function () {
        return $cookies.get('token');
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
      }
    };
    return service;

    /**
   * Go to login state if user is not authenticated
   * @param $state: state object
     */
    function goToLogin($state){
      if (!service.is_authenticated_user()) {
        $state.go('login');
      }
      return service.is_authenticated_user();
    }
  }
})();
