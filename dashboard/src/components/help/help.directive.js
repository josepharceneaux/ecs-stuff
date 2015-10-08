(function () {

    'use strict';

    angular.module('app.help')
        .directive('gtHelp', directiveFunction)
        .controller('HelpController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/help/help.html',
            scope: {
            },
            controller: 'HelpController',
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
            logger.log('Activated Help View');
        }
    }

})();
