(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtUserProfile', directiveFunction)
        .controller('UserProfileController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/user-profile/user-profile.html',
            replace: true,
            scope: {},
            controller: 'UserProfileController',
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
            logger.log('Activated User Profile View');
        }

        function init() {
            //
        }
    }
})();
