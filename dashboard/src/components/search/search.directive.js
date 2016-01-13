(function () {
    'use strict';

    angular
        .module('app.search')
        .directive('gtSearch', directiveFunction)
        .controller('SearchController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/search/search.html',
            replace: true,
            scope: {
            },
            controller: 'SearchController',
            controllerAs: 'vm',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated Search View');
        }
    }

    function linkFunction(scope, elem, attrs) {
        //
    }
})();
