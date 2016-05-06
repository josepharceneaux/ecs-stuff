(function() {
  'use strict';

  angular
    .module('app.scheduler_admin')
    .run(appRun);

  appRun.$inject = ['routerHelper'];
  /* @ngInject */
  function appRun(routerHelper) {
    routerHelper.configureStates(getStates());
  }

  function getStates() {
    return [
      {
        state: 'scheduler_admin',
        config: {
          url: '/scheduler_admin',
          templateUrl: 'app/scheduler_admin/scheduler_admin.html',
          controller: 'SchedulerAdminController',
          controllerAs: 'vm',
          is_authenticated: true,
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
