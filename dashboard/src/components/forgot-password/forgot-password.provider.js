(function () {
    'use strict';

    angular
        .module('app.candidates')
        .provider('forgotPasswordService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['userService'];

        /* @ngInject */
        function $get(userService) {
            return {
                sendForgotPasswordRequest: sendForgotPasswordRequest
            };

            function sendForgotPasswordRequest(username) {
                var payload = {
                    username: username
                };
                return userService.all('users').customPOST(payload, 'forgot_password').then(function (response) {
                    return response;
                });
            }
        }
    }

})();
