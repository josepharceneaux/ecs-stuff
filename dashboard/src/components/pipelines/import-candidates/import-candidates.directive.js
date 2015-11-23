(function () {

    'use strict';

    angular.module('app.pipelines')
        .directive('gtImportCandidates', directiveFunction)
        .controller('ImportCandidatesController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/import-candidates/import-candidates.html',
            replace: true,
            scope: {
            },
            controller: 'ImportCandidatesController',
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
            logger.log('Activated Import Candidates View');
        }
    }

})();
