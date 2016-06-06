(function() {
  'use strict';

  angular
    .module('app.scheduler_admin')
    .controller('SchedulerAdminController', SchedulerAdminController);

  SchedulerAdminController.$inject = ['logger','$state', '$rootScope', 'UserToken', 'SchedulerClientService'];
  /* @ngInject */
  function SchedulerAdminController(logger, $state, $rootScope, UserToken, SchedulerClientService) {
    var vm = this;
    vm.title = 'Scheduler Service Admin';

    UserToken.goToLogin();

    vm.apply_filter = function(){

      var filter_dict = {};

      if(vm.selected_task_type !== "both"){
        filter_dict['task_type'] = vm.selected_task_type;
      }

      if(vm.selected_task_category !== "both")
        filter_dict['task_category'] = vm.selected_task_category;

      if(typeof vm.user_id == "number" && vm.user_id >= 1 && vm.selected_task_category != "general")
        filter_dict['user_id'] = vm.user_id;

      if(vm.paused.enabled)
        filter_dict['paused'] = vm.paused.enabled;

      filter_dict['per_page'] = vm.itemsPerPage;
      filter_dict['page'] = vm.currentPage;

      SchedulerClientService.getTasks(filter_dict)
      .then(function (response) {
        if ("tasks" in response.data) {

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
        sInfoEmpty: "",
        sInfo: "",
        sEmptyTable: "No jobs available"
      }
    };

    vm.setPage = function (pageNo) {
      $scope.currentPage = pageNo;
    };

    vm.pageChanged = function() {
      vm.apply_filter();
    };

    vm.itemsPerPage = 15;

    vm.paused = { name: 'Paused only', enabled: false };

    vm.selected_task_type = "both";

    vm.task_type = [
      {id: 1, title: " Both", value: "both"},
      {id: 2, title: " Periodic", value: "periodic"},
      {id: 3, title: "One Time", value: "one_time"}
    ];

    vm.selected_task_category = "both";
    vm.task_category = [
      {id: 1, title: " Both", value: "both"},
      {id: 2, title: " User", value: "user"},
      {id: 3, title: "General", value: "general"}
    ];

    function activate() {
      logger.info('Activated Scheduler Admin View');

      $rootScope.$on('loggedIn', function (events, args) {
          vm.currentPage = 1;
      });
    }

    UserToken.goToLogin($state);

    activate();
  }
})();
