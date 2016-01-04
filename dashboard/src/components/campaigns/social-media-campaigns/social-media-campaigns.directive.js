(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtSocialMediaCampaigns', directiveFunction)
        .controller('SocialMediaCampaignsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/social-media-campaigns/social-media-campaigns.html',
            scope: {
            },
            controller: 'SocialMediaCampaignsController',
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
            logger.log('Activated SocialMedia Campaigns View');
        }
    }
})();
