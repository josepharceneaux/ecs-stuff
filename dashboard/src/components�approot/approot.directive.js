(function () {
    'use strict';

    angular.module('app.approot')
        .directive('gtApproot', directiveFunction)
        .controller('RootController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/approot/approot.html',
            replace: true,
            scope: {},
            controller: 'RootController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'logger'];

    /* @ngInject */
    function ControllerFunction($state, logger) {
        var vm = this;

        init();
        activate();

        function init() {
            vm.state = $state;

            /* https://code.angularjs.org/1.4.8/docs/api/ng/directive/ngModelOptions */
            vm.ngModelOptions = {};
            vm.ngModelOptions.allowInvalid = true;
            //vm.ngModelOptions.updateOn: 'default';
            //vm.ngModelOptions.debounce = { 'default': 500, 'blur': 0 };
        }

        function activate() {
            logger.log('Activated Root View');
        }
    }
})();
