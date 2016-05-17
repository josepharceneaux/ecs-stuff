(function() {
  'use strict';

  angular
    .module('app.scheduler_admin')
    .controller('SchedulerAdminController', SchedulerAdminController);

  SchedulerAdminController.$inject = ['logger', 'AuthUser'];
  /* @ngInject */
  function SchedulerAdminController(logger, AuthUser) {
    var vm = this;
    vm.title = 'Scheduler Service Admin';

    activate();

    function activate() {
      logger.info('Activated Scheduler Admin View');
    }
  }
})();
