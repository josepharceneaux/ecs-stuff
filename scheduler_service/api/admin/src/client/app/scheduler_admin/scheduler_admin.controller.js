(function() {
  'use strict';

  angular
    .module('app.scheduler_admin')
    .controller('SchedulerAdminController', SchedulerAdminController);

  SchedulerAdminController.$inject = ['logger'];
  /* @ngInject */
  function SchedulerAdminController(logger) {
    var vm = this;
    vm.title = 'Scheduler Service Admin';

    activate();

    function activate() {
      logger.info('Activated Scheduler Admin View');
    }
  }
})();
