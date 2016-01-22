(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminUsers', directiveFunction)
        .controller('AdminUsersController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-users/admin-users.html',
            replace: true,
            scope: {},
            controller: 'AdminUsersController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$cookies', 'logger'];

    /* @ngInject */
    function ControllerFunction($cookies, logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated Admin Users View');
        }
    }
})();
