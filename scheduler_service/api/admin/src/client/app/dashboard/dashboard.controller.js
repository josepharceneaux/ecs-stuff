(function() {
  'use strict';

  angular
    .module('app.dashboard')
    .controller('DashboardController', DashboardController);

  DashboardController.$inject = ['$q', '$location', 'logger', 'AuthUser'];
  /* @ngInject */
  function DashboardController($q, $location, logger, AuthUser) {
    var vm = this;
    vm.news = {
      title: 'Scheduler Service Admin Panel',
      description: ''
    };
    vm.messageCount = 0;
    vm.people = [];
    vm.title = 'Dashboard';

    if(!AuthUser.is_authenticated){
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
