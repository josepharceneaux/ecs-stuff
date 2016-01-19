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
    ControllerFunction.$inject = ['$cookies', 'logger'];

    /* @ngInject */
    function ControllerFunction($cookies, logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated Admin User Add View');
        }
    }
})();
