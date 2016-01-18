(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEmailEdit', directiveFunction)
        .controller('CampaignEmailEditController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-emails/campaign-email-edit/campaign-email-edit.html',
            replace: true,
            scope: {},
            controller: 'CampaignEmailEditController',
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
            logger.log('Activated Campaign Email Edit View');
        }
    }
})();
