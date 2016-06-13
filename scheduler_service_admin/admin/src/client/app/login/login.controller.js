(function () {
  'use strict';

  angular
    .module('app.login')
    .controller('LoginController', LoginController);

  LoginController.$inject = ['logger', '$state', 'UserToken'];
  /* @ngInject */

  function LoginController(logger, $state, UserToken) {
    var vm = this;
    vm.title = 'Login';

    /**
     * Send request to user service and check if user has admin rights to access scheduler jobs or not
     * @param _response
     * @returns {boolean}
     */
    function isUserAdmin(_response) {

      if (_response.status === 200) {
        for (var index = 0; index < _response.data.roles.length; index++) {
          var role = _response.data.roles[index];
          if (role.name === 'CAN_GET_ALL_SCHEDULER_JOBS') {
            return true;
          }
        }
      }
      return false;
    }

    /**
     * Login and then check if user has privileges to access scheduler service admin API.
     * If yes, then navigate to scheduler admin page.
     * Otherwise throw unauthorized exception
     */
    vm.login = function () {

      UserToken.loginUser(vm.email, vm.password)
        .then(function (response) {
          if (response.status === 200 && 'access_token' in response.data) {
            UserToken.testAuthenticateUserRole(response.data['user_id'], response.data.access_token)
              .then(function (_response) {

                if (isUserAdmin(_response)) {
                  UserToken.authenticateUser(response.data);
                  logger.info('User authenticated successfully.');
                  $state.go('schedulerAdmin');
                }
              }, error);
          }
        }, error);

      /**
       * Show error message to user
       * @param err
       */
      function error(err) {
        vm.error_message = 'Unauthorized: You don\'t have access to get-Talent';
        logger.error(err);
      }
    };

    activate();

    function activate() {
      logger.info('Activated Login')
    }
  }
})();
