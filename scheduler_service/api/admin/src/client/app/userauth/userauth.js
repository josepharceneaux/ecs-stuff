/**
 * Created by saad on 5/16/16.
 */

(function() {
  'use strict';

  angular
    .module('app.userauth')
    .factory('AuthUser', AuthUser);
  /* @ngInject */
  function AuthUser() {

    return {
      access_token: null,
      refresh_token: null,
      is_authenticated: false
    };
  }
});
