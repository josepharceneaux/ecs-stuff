(function() {
  'use strict';

  angular
    .module('app.layout')
    .controller('ShellController', ShellController);

  ShellController.$inject = ['$rootScope', '$timeout', 'config', 'logger', 'UserToken'];
  /* @ngInject */
  function ShellController($rootScope, $timeout, config, logger, UserToken) {
    var vm = this;
    vm.busyMessage = 'Please wait ...';
    vm.isBusy = true;
    $rootScope.showSplash = true;
    vm.navline = {
      title: config.appTitle,
      text: 'get-talent Admin',
      link: '#'
    };

    vm.loggedIn = UserToken.is_authenticated_user() ? true: false;

    $rootScope.$on('loggedIn',
      function (events, args) {
        vm.loggedIn = args;
      });

    activate();

    function activate() {
      logger.success(config.appTitle + ' loaded!', null);
      hideSplash();
    }

    function hideSplash() {
      //Force a 1 second delay so we can see the splash.
      $timeout(function() {
        $rootScope.showSplash = false;
      }, 1000);
    }
  }
})();
