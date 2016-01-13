(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEmailCreate', directiveFunction)
        .controller('CampaignEmailCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-emails/campaign-email-create/campaign-email-create.html',
            scope: {
            },
            controller: 'CampaignEmailCreateController',
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
            logger.log('Activated Campaign Email Create View');
        }
    }
})();
