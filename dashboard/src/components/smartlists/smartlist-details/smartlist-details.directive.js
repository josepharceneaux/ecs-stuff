(function () {
    'use strict';

    angular.module('app.smartlists')
        .directive('gtSmartlistDetails', directiveFunction)
        .controller('SmartlistDetailsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/smartlists/smartlist-details/smartlist-details.html',
            replace: true,
            scope: {},
            controller: 'SmartlistDetailsController',
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
            logger.log('Activated Smartlist Details View');
        }

    }
})();
