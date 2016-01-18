(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminSettings', directiveFunction)
        .controller('AdminSettingsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-settings/admin-settings.html',
            replace: true,
            scope: {},
            controller: 'AdminSettingsController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$cookies', 'logger'];

    /* @ngInject */
    function ControllerFunction($cookies, logger) {
        var vm = this;

        vm.setDemoModeCookie = setDemoModeCookie;

        activate();

        function activate() {
            logger.log('Activated Admin Settings View');

            vm.demoMode = getDemoModeCookie();
        }

        function getDemoModeCookie() {
            return $cookies.get('demoMode') === 'true';
        }

        function setDemoModeCookie(value) {
            $cookies.put('demoMode', value === 'true' || value === true ? 'true' : 'false');
        }
    }
})();
