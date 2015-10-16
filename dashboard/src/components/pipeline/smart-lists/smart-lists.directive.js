(function () {

    'use strict';

    angular.module('app.pipeline')
        .directive('gtSmartLists', directiveFunction)
        .controller('SmartListsController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipeline/smart-lists/smart-lists.html',
            scope: {
            },
            controller: 'SmartListsController',
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
            logger.log('Activated Smart Lists View');
        }
    }

})();
