(function () {
    'use strict';

    angular
        .module('app.notificationCenter')
        .provider('notificationService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['activityService'];

        /* @ngInject */
        function $get(activityService) {
            var notificationService = activityService.withConfig(function (RestangularConfigurer) {
            });

            return {
                getActivity: getActivity
            };

            function getActivity(page, aggregate) {
                var params = {};
                page = page || 1;
                aggregate = aggregate || 1;
                //params['aggregate'] = aggregate;
                return notificationService.all('activities').customGETLIST(page, params);
            }
        }
    }

})();
