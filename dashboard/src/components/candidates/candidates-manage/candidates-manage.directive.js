(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateManage', directiveFunction)
        .controller('CandidateManageController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-manage/candidate-manage.html',
            replace: true,
            scope: {
            },
            controller: 'CandidateManageController',
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
            logger.log('Activated Candidate Manage View');
        }

        function init() {
            //
        }
    }
})();
