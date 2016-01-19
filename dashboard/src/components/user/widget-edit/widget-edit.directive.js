(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtWidgetEdit', directiveFunction)
        .controller('WidgetEditController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/widget-edit/widget-edit.html',
            replace: true,
            scope: {},
            controller: 'WidgetEditController',
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
            logger.log('Activated Widget Edit View');
        }

        function init() {
            //
        }
    }
})();
