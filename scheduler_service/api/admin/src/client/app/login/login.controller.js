(function() {
  'use strict';

  angular
    .module('app.login')
    .controller('LoginController', LoginController);

  LoginController.$inject = ['logger', '$state', 'UserToken'];
  /* @ngInject */
  function LoginController(logger, $state, UserToken) {
    var vm = this;
    vm.title = 'Login';

    UserToken.goToLogin($state);

    activate();

    function activate() {

    }
  }
})();
