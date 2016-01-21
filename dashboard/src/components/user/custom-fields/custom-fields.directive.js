(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtCustomFields', directiveFunction)
        .controller('CustomFieldsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/custom-fields/custom-fields.html',
            replace: true,
            scope: {},
            controller: 'CustomFieldsController',
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
            logger.log('Activated Custom Fields View');
        }

        function init() {
            //
        }
    }
})();
