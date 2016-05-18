(function() {
  'use strict';

  angular
    .module('app.dashboard')
    .controller('DashboardController', DashboardController);

  DashboardController.$inject = ['$q', '$location', 'logger', 'usertoken'];

  /* @ngInject */
  function DashboardController($q, $location, logger, usertoken) {

    var vm = this;
    vm.news = {
      title: 'Scheduler Service Admin Panel',
      description: ''
    };
    vm.messageCount = 0;
    vm.people = [];
    vm.title = 'Dashboard';

    if(!usertoken.is_authenticated){
      logger.info('User not authenticated. Navigating to Login page.');
      $location.path('/user/login');
      //$location.url('/user/login');
    }

    activate();

    function activate() {
      var promises = [];
      return $q.all(promises).then(function() {
        logger.info('Activated Dashboard View');
      });
    }
  }
})();
