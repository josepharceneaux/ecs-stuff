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
    ControllerFunction.$inject = ['logger', 'candidatesManageService'];

    /* @ngInject */
    function ControllerFunction(logger, candidatesManageService) {
        var vm = this;

        vm.itemsPerPageOptions = [
            { value: 5, name: '5 per page' },
            { value: 10, name: '10 per page' },
            { value: 15, name: '15 per page' }
        ];
        vm.candidatesPerPage = vm.itemsPerPageOptions[0].value;

        init();
        activate();

        function activate() {
            logger.log('Activated Candidates Manage View');
        }

        function init() {
            candidatesManageService.getCandidates().then(function (candidates) {
                vm.candidates = candidates;
            });
        }
    }
})();
