(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtSettings', directiveFunction)
        .controller('SettingsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/settings/settings.html',
            replace: true,
            scope: {},
            controller: 'SettingsController',
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
            logger.log('Activated Settings View');
        }

        function init() {
            //
        }
    }
})();
