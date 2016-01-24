(function () {
    'use strict';

    angular
        .module('app.admin')
        .provider('adminUsersService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['userService'];

        /* @ngInject */
        function $get(userService) {

            return {
                createUser: createUser,
                createUsers: createUsers
            };

            function createUser(user) {
                var users = [ user ];
                return createUsers(users);
            }

            function createUsers(users) {
                return userService.all('users').post(users);
            }
        }
    }

})();
