(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtWidgetOptions', directiveFunction)
        .controller('WidgetOptionsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/widget-options/widget-options.html',
            replace: true,
            scope: {},
            controller: 'WidgetOptionsController',
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
            logger.log('Activated Widget Options View');
        }

        function init() {
            //
        }
    }
})();
