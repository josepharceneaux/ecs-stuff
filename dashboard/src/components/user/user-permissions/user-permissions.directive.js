(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtUserPermissions', directiveFunction)
        .controller('UserPermissionsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/user-permissions/user-permissions.html',
            replace: true,
            scope: {},
            controller: 'UserPermissionsController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated User Permissions View');
        }

        function init() {
            //
        }
    }
})();
