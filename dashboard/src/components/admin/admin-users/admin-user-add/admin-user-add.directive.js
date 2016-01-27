(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminUserAdd', directiveFunction)
        .controller('AdminUserAddController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-users/admin-user-add/admin-user-add.html',
            replace: true,
            scope: {},
            controller: 'AdminUserAddController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'logger', 'adminUsersService', 'systemAlertsService'];

    /* @ngInject */
    function ControllerFunction($state, logger, adminUsersService, systemAlertsService) {
        var vm = this;

        vm.createUser = createUser;

        activate();

        function activate() {
            logger.log('Activated Admin User Add View');
        }

        function createUser(user) {
            adminUsersService.createUser(user).then(function (response) {
                var userId = response.users[0];
                if (userId) {
                    systemAlertsService.createAlert('User <strong>$userName</strong> successfully created.'.replace('$userName', user.userName));
                    $state.go('admin.users');
                }
            });
        }

    }
})();
