/**
 * Created by erikfarmer on 2/16/16.
 */

(function() {
    'use strict';

    angular
        .module('app')
        .controller('HomeController', controllerFunction);

    controllerFunction.$inject = ['$timeout']

    function controllerFunction($timeout) {
        var vm = this;
        vm.state = 'form';
        vm.firstName;
        vm.lastName;
        vm.phone;
        vm.email;
        vm.mockSubmit = mockSubmit;

        function mockSubmit() {
            vm.state = 'submit';
            $timeout(function() {
                vm.firstName = null;
                vm.lastName = null;
                vm.phone = null;
                vm.email = null;
                vm.state = 'form'
            }, 10000);
        }

    }
})();