(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtOrganizationInvite', directiveFunction)
        .controller('OrganizationInviteController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/organization-invite/organization-invite.html',
            replace: true,
            scope: {},
            controller: 'OrganizationInviteController',
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
            logger.log('Activated Organization Invite View');
        }

        function init() {
            //
        }
    }
})();
