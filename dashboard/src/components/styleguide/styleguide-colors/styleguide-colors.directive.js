(function () {
    'use strict';

    angular.module('app.styleguide')
        .directive('gtStyleguideColors', directiveFunction)
        .controller('StyleguideColorsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/styleguide/styleguide-colors/styleguide-colors.html',
            replace: true,
            scope: {},
            controller: 'StyleguideColorsController',
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
            logger.log('Activated Styleguide Colors View');
        }
    }
})();
