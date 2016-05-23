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

     SchedulerClientService.getTasks(4)
      .then(function (data) {
        if ("tasks" in data) {
          vm.tasks = data.tasks;
          console.log(vm.tasks);
        }
      }, function (error) {
        console.log('error', error);
      });
    //debugger;


    activate();

    function activate() {
      logger.info('Activated Scheduler Admin View');
    }
  }
})();
