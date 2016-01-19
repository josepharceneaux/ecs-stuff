(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminUserEdit', directiveFunction)
        .controller('AdminUserEditController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-users/admin-user-edit/admin-user-edit.html',
            replace: true,
            scope: {},
            controller: 'AdminUserEditController',
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
            logger.log('Activated Admin User Edit View');
        }
    }
})();
