(function () {

    'use strict';

    angular.module('app.pipeline')
        .directive('gtImportCandidates', directiveFunction)
        .controller('ImportCandidatesController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipeline/import-candidates/import-candidates.html',
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
