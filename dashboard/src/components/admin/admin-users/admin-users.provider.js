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

        $get.$inject = ['$q', 'userService'];

        /* @ngInject */
        function $get($q, userService) {

            return {
                createUser: createUser,
                createUsers: createUsers,
                getUser: getUser,
                getUserIds: getUserIds,
                getUsers: getUsers
            };

            function createUser(user) {
                var users = [ user ];
                return createUsers(users);
            }

            function createUsers(users) {
                return userService.all('users').post(users);
            }

            function getUser(id) {
                return userService.one('users', id).get();
            }

            function getUserIds() {
                return userService.all('users').getList();
            }

            function getUsers() {
                var users = [];
                var requests = [];
                var deferred = $q.defer();
                deferred.promise.$object = users;
                getUserIds().then(function (ids) {
                    ids.forEach(function (id) {
                        var request = getUser(id);
                        request.then(function (user) {
                            users.push(user.user);
                        });
                        requests.push(request);
                    });
                    $q.when(requests).then(function () {
                        deferred.resolve(users);
                    });
                });
                return deferred.promise;
            }
        }
    }

})();
