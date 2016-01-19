(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtEmailMarketing', directiveFunction)
        .controller('EmailMarketingController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/email-marketing/email-marketing.html',
            replace: true,
            scope: {},
            controller: 'EmailMarketingController',
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
            logger.log('Activated Email Marketing View');
        }

        function init() {
            //
        }
    }
})();
