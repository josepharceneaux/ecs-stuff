(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtSmartlistCreate', directiveFunction)
        .controller('SmartlistCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/smartlists/smartlist-create/smartlist-create.html',
            replace: true,
            scope: {},
            controller: 'SmartlistCreateController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {

        activate();

        function activate() {
            logger.log('Activated Smartlist Create View');
        }
    }
})();
