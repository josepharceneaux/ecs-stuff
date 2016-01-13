(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEmailDetail', directiveFunction)
        .controller('CampaignEmailDetailController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-emails/campaign-email-detail/campaign-email-detail.html',
            scope: {
            },
            controller: 'CampaignEmailDetailController',
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
            logger.log('Activated Campaign Email Detail View');
        }
    }
})();
