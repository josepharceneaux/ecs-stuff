(function() {
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
    function TopNavController($scope, UserToken, $state) {
      var vm = this;
      $scope.isCollapsed = true;

      vm.loggedIn = UserToken.access_token !== "";

      vm.logout_user = function () {

          UserToken.logout_user();
          UserToken.goToLogin($state);
      };

      $rootScope.$on('loggedIn', function (events, args) {
          vm.loggedIn = args;
      });

    }

    return directive;
  }
})();
