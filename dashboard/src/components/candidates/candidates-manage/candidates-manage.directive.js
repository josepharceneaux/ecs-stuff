(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidatesManage', directiveFunction)
        .controller('CandidatesManageController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidates-manage/candidates-manage.html',
            replace: true,
            scope: {},
            controller: 'CandidatesManageController',
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
            logger.log('Activated Candidates Manage View');
        }

        function init() {
            //
        }
    }
})();
