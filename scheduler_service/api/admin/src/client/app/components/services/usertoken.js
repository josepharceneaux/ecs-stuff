/**
 * Created by saad on 5/16/16.
 */

(function() {
  'use strict';

  angular
    .module('app.components')
    .factory('UserToken', UserToken);
  /* @ngInject */
  function UserToken() {

    var service = {
      access_token: '9ery8pVOxTOvQU0oJsENRek4lj6ZT6',
      refresh_token: 'oRojE4Gu4KY29TXO11yh1AcZLGjOhM',
      is_authenticated: true,
      goToLogin: goToLogin
    };
    return service;

    /**
   * Go to login state if user is not authenticated
   * @param $state: state object
     */
    function goToLogin($state){
      if (service.is_authenticated === false) {
        $state.go('login');
      }
    }
  }
})();
