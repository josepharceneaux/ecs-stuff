/**
 * Scheduler Admin controller which get data from external talent-flask services (i.e. scheduler service) and then
 * using filters and show them in UI
 */
(function() {
  'use strict';

  angular
    .module('app.schedulerAdmin')
    .controller('SchedulerAdminController', SchedulerAdminController);

  SchedulerAdminController.$inject = ['logger', '$rootScope', 'UserToken', 'SchedulerClientService'];
  /* @ngInject */
  function SchedulerAdminController(logger, $rootScope, UserToken, SchedulerClientService) {
    var vm = this;
    vm.title = 'Scheduler Service Admin';
    var both_tasks = 'both';
    var general_tasks = 'general';

    // Navigate to login state if user is not logged in
    UserToken.goToLogin();

    /**
     * Get filtered jobs from scheduler service and show them in data table (UI)
     */
    vm.applyFilter = function(){

      var filterDict = {};

      if(vm.selectedTaskType !== both_tasks){
        filterDict['task_type'] = vm.selectedTaskType;
      }

      if(vm.selectedTaskCategory !== both_tasks) {
        filterDict['task_category'] = vm.selectedTaskCategory;
      }

      if(typeof vm.userId === 'number' && vm.userId >= 1 && vm.selectedTaskCategory !== general_tasks) {
        filterDict['user_id'] = vm.userId;
      }

      if(vm.paused.enabled) {
        filterDict['paused'] = vm.paused.enabled;
      }

      filterDict['per_page'] = vm.itemsPerPage;
      filterDict['page'] = vm.currentPage;

      SchedulerClientService.getTasks(filterDict)
      .then(function (response) {
        if ('tasks' in response.data) {

          vm.tasks = response.data.tasks;
          vm.totalItems = response.headers('X-Total');
          vm.currentPage = response.headers('X-Page');
          vm.itemsPerPage = response.headers('X-Per-Page');
        }
      }, function (error) {
        logger.error('error', error);
      });
    };

    // Active Responsive plugin
    vm.dtOptions = {
      responsive: true,
      paging: false,
      searching: false,
      language: {
        sInfoEmpty: '',
        sInfo: '',
        sEmptyTable: 'No jobs available'
      }
    };

    vm.setPage = function (pageNo) {
      vm.currentPage = pageNo;
    };

    vm.pageChanged = function() {
      vm.applyFilter();
    };

    vm.itemsPerPage = 15;

    vm.paused = { name: 'Paused only', enabled: false };

    vm.selectedTaskType = both_tasks;

    vm.taskType = [
      {id: 1, title: ' Both', value: both_tasks},
      {id: 2, title: ' Periodic', value: 'periodic'},
      {id: 3, title: 'One Time', value: 'one_time'}
    ];

    vm.selectedTaskCategory = both_tasks;
    vm.taskCategory = [
      {id: 1, title: ' Both', value: both_tasks},
      {id: 2, title: ' User', value: 'user'},
      {id: 3, title: 'General', value: general_tasks}
    ];

    function activate() {
      logger.info('Activated Scheduler Admin View');

      $rootScope.$on('loggedIn', function (events, args) {
          vm.currentPage = 1;
        vm.applyFilter()
      });
    }

    activate();
  }
})();
