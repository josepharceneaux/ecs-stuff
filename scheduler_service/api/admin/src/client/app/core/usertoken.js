/**
 * Created by saad on 5/16/16.
 */

(function() {
  'use strict';

  angular
    .module('app.core')
    .factory('usertoken', usertoken);
  /* @ngInject */
  function usertoken() {

    var service = {
      access_token: null,
      refresh_token: null,
      is_authenticated: false
    };
    return service;
  }
})();
