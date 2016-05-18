(function() {
  'use strict';

  angular
    .module('app.scheduler_admin')
    .controller('SchedulerAdminController', SchedulerAdminController);

  SchedulerAdminController.$inject = ['logger','$state', 'UserToken', 'SchedulerClientService'];
  /* @ngInject */
  function SchedulerAdminController(logger, $state, UserToken, SchedulerClientService) {
    var vm = this;
    vm.title = 'Scheduler Service Admin';

    UserToken.goToLogin($state);
    activate();

    console.log(SchedulerClientService.getTasks(4));

    function activate() {
      logger.info('Activated Scheduler Admin View');
    }
  }
})();
