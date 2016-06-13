(function () {
  'use strict';

  angular
    .module('app.layout')
    .directive('htTopNav', htTopNav);

  /* @ngInject */
  function htTopNav($rootScope) {
    var directive = {
      bindToController: true,
      controller: TopNavController,
      controllerAs: 'vm',
      restrict: 'EA',
      scope: {
        'navline': '='
      },
      templateUrl: 'app/layout/ht-top-nav.html'
    };

    TopNavController.$inject = ['$scope', 'UserToken', '$state'];

    /* @ngInject */
    function TopNavController($scope, UserToken) {
      var vm = this;
      $scope.isCollapsed = true;

      vm.loggedIn = UserToken.accessToken !== '';

      vm.logoutUser = function () {

        UserToken.logoutUser();
        UserToken.goToLogin();
      };

      $rootScope.$on('loggedIn', function (events, args) {
        vm.loggedIn = args;
      });

    }

    return directive;
  }
})();
