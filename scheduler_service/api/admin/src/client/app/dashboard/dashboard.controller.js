(function() {
  'use strict';

  angular
    .module('app.dashboard')
    .controller('DashboardController', DashboardController);

  DashboardController.$inject = ['$q', '$state', '$location', 'logger', 'UserToken'];

  /* @ngInject */
  function DashboardController($q, $state, $location, logger, UserToken) {

    var vm = this;
    vm.news = {
      title: 'Scheduler Service Admin Panel',
      description: ''
    };
    vm.messageCount = 0;
    vm.people = [];
    vm.title = 'Dashboard';

    UserToken.goToLogin($state);

    activate();

    function activate() {
      var promises = [];
      return $q.all(promises).then(function() {
        logger.info('Activated Dashboard View');
      });
    }
  }
})();
