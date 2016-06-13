(function() {
  'use strict';

  angular
    .module('app.schedulerAdmin')
    .run(appRun);

  appRun.$inject = ['routerHelper'];
  /* @ngInject */
  function appRun(routerHelper) {
    routerHelper.configureStates(getStates());
  }

  function getStates() {
    return [
      {
        state: 'schedulerAdmin',
        config: {
          url: '/',
          templateUrl: 'app/schedulerAdmin/schedulerAdmin.html',
          controller: 'SchedulerAdminController',
          controllerAs: 'vm',
          title: 'Scheduler Service',
          settings: {
            nav: 2,
            content: '<i class="fa fa-lock"></i> Scheduler Service'
          }
        }
      }
    ];
  }
})();
