(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtWidgetAdd', directiveFunction)
        .controller('WidgetAddController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/widget-add/widget-add.html',
            replace: true,
            scope: {},
            controller: 'WidgetAddController',
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
            logger.log('Activated Widget Add View');
        }

        function init() {
            //
        }
    }
})();
