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


    UserToken.goToLogin();

    /**
     * Get filtered jobs from scheduler service and shows them in data table (UI)
     */
    vm.applyFilter = function(){

      var filterDict = {};

      if(vm.selectedTaskType !== 'both'){
        filterDict['task_type'] = vm.selectedTaskType;
      }

      if(vm.selectTaskCategory !== 'both') {
        filterDict['task_category'] = vm.selectTaskCategory;
      }

      if(typeof vm.userId === 'number' && vm.userId >= 1 && vm.selectTaskCategory !== 'general') {
        filterDict['userId'] = vm.userId;
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

    vm.selectedTaskType = 'both';

    vm.taskType = [
      {id: 1, title: ' Both', value: 'both'},
      {id: 2, title: ' Periodic', value: 'periodic'},
      {id: 3, title: 'One Time', value: 'one_time'}
    ];

    vm.selectTaskCategory = 'both';
    vm.taskCategory = [
      {id: 1, title: ' Both', value: 'both'},
      {id: 2, title: ' User', value: 'user'},
      {id: 3, title: 'General', value: 'general'}
    ];

    function activate() {
      logger.info('Activated Scheduler Admin View');

      $rootScope.$on('loggedIn', function (events, args) {
          vm.currentPage = 1;
      });
    }

    activate();
  }
})();
