(function() {
  'use strict';

  angular
    .module('app.login')
    .controller('LoginController', LoginController);

  LoginController.$inject = ['logger', 'AuthUser'];
  /* @ngInject */
  function LoginController(logger, AuthUser) {
    var vm = this;
    vm.title = 'Login';

    activate();

    function activate() {

    }
  }
})();
