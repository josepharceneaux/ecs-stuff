(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidatesOverview', directiveFunction)
        .controller('CandidatesOverviewController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidates-overview/candidates-overview.html',
            replace: true,
            scope: {
            },
            controller: 'CandidatesOverviewController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Candidates Overview View');
        }

        function init() {
            //
        }
    }
})();
