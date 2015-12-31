// -------------------------------------
//   Tabs
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtPane', directiveFunction)
        .controller('PaneController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            require: ['^gtTabs', 'gtPane'],
            templateUrl: 'core/modules/tabs/pane.html',
            replace: true,
            transclude: true,
            scope: {
                title: '@'
            },
            bindToController: true,
            controller: 'PaneController',
            controllerAs: 'paneCtrl',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;
        vm.selected = false;
    }

    function linkFunction(scope, elem, attrs, ctrls) {
        var tabsCtrl = ctrls[0];
        var paneCtrl = ctrls[1];

        tabsCtrl.addPane(paneCtrl);
    }
})();
