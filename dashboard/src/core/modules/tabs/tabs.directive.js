// -------------------------------------
//   Tabs
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtTabs', directiveFunction)
        .controller('TabsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'core/modules/tabs/tabs.html',
            replace: true,
            transclude: true,
            scope: {},
            bindToController: true,
            controller: 'TabsController',
            controllerAs: 'tabsCtrl',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;

        vm.panes = [];

        vm.select = select;
        vm.addPane = addPane;

        function select(pane) {
            angular.forEach(vm.panes, function (pane) {
                pane.selected = false;
            });
            pane.selected = true;
        }

        function addPane(pane) {
            if (vm.panes.length === 0) vm.select(pane);
            vm.panes.push(pane);
        }
    }

    function linkFunction(scope, elem, attrs, ctrls) {
        init();

        ///////////////

        function init() {
        }
    }
})();
