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

            function getActivity() {
                return notificationService.all('activities').all('1').getList('1');
            }
        }
    }

})();
