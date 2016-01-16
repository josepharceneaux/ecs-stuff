(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtOrganization', directiveFunction)
        .controller('OrganizationController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/organization/organization.html',
            replace: true,
            scope: {},
            controller: 'OrganizationController',
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
            logger.log('Activated Organization View');
        }

        function init() {
            //
        }
    }
})();
