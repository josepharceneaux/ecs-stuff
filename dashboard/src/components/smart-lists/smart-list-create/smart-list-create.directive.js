(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtSmartListCreate', directiveFunction)
        .controller('SmartListCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/smart-lists/smart-list-create/smart-list-create.html',
            replace: true,
            scope: {
            },
            controller: 'SmartListCreateController',
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
            logger.log('Activated Smart List Create View');
        }
    }
})();
