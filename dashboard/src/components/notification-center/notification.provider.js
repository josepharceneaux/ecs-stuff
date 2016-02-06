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
             var mappings = {
                    1: { icon: 'icon--candidate', class: 'candidate'},
                    2: { icon: 'icon--candidate', class: 'candidate'},
                    3: { icon: 'icon--candidate', class: 'candidate'},
                    4: { icon: 'icon--campaigns', class: 'campaigns'},
                    5: { icon: 'icon--campaigns', class: 'campaigns'},
                    6: { icon: 'icon--campaigns', class: 'campaigns'},
                    7: { icon: 'icon--campaigns', class: 'campaigns'},
                    8: { icon: 'icon--smartlists', class: 'smartlists'},
                    9: { icon: 'icon--smartlists', class: 'smartlists'},
                    10: { icon: 'icon--smartlists', class: 'smartlists'},
                    11: { icon: 'icon--smartlists', class: 'smartlists'},
                    12: { icon: 'icon--users', class: 'users'},
                    13: { icon: 'icon--widget', class: 'widget'},
                    14: { icon: 'icon--notifications', class: 'notifications'},
                    15: { icon: 'icon--campaigns', class: 'campaigns'},
                    16: { icon: 'icon--campaigns', class: 'campaigns'},
                    17: { icon: 'icon--campaigns', class: 'campaigns'},
                    18: { icon: 'icon--candidate', class: 'candidate'},
                    19: { icon: 'icon--candidate', class: 'candidate'},
                    20: { icon: 'icon--candidate', class: 'candidate'},
                    21: { icon: 'icon--campaigns', class: 'campaigns'},
                    22: { icon: 'icon--campaigns', class: 'campaigns'},
                    123: { icon: 'icon--rspvs', class: 'rspvs'}
                };

            function getCss(type){
                if (type in mappings) {
                    return mappings[type];
                }
                return {icon: 'icon--default', class: 'default'}
            }

            return {
                getActivity: getActivity,
                getActivityMessages: getActivityMessages,
                getCss: getCss
            };

            function getActivity(page, aggregate) {
                var params = {};
                page = page || 1;
                aggregate = aggregate || 1;
                //params['aggregate'] = aggregate;
                return notificationService.all('activities').customGETLIST(page, params);
            }
            function getActivityMessages() {
                return notificationService.all('messages').getList();
            }
        }
    }

})();
