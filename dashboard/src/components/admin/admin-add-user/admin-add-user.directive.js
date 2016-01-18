(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminAddUser', directiveFunction)
        .controller('AdminAddUserController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-add-user/admin-add-user.html',
            replace: true,
            scope: {},
            controller: 'AdminAddUserController',
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
            logger.log('Activated Admin Add User View');
        }
    }
})();
