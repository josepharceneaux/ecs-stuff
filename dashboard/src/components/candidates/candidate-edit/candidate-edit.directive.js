(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateEdit', directiveFunction)
        .controller('CandidateEditController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-edit/candidate-edit.html',
            replace: true,
            scope: {},
            controller: 'CandidateEditController',
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
            logger.log('Activated Candidate Edit View');
        }

        function init() {
            //
        }
    }
})();
