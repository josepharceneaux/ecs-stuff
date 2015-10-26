(function () {
    'use strict';

    angular
        .module('app.footer')
        .directive('gtFooter', directiveFunction)
        .controller('FooterController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/footer/footer.html',
            scope: {
            },
            controller: 'FooterController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;
        vm.isCollapsed = true;
    }

})();
