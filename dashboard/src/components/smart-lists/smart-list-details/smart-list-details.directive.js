(function () {
    'use strict';

    angular.module('app.smartLists')
        .directive('gtSmartListDetails', directiveFunction)
        .controller('SmartListDetailsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/smart-lists/smart-list-details/smart-list-details.html',
            replace: true,
            scope: {},
            controller: 'SmartListDetailsController',
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
            logger.log('Activated Smart List Details View');
        }
    }
})();
