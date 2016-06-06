(function() {
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
     * Send request to user service and check if user is admin or not
     * @param _response
     * @returns {boolean}
       */
    function isUserAdmin(_response){

      if(_response.status == 200) {
        for(var index=0;index < _response.data.roles.length;index++){
          var role = _response.data.roles[index];
          if(role.name === "CAN_GET_ALL_SCHEDULER_JOBS"){
            return true;
          }
        }
      }
      return false;
    }

    vm.login = function () {

      UserToken.login_user(vm.email, vm.password)
      .then(function (response) {
          if(response.status == 200 && "access_token" in response.data){
            UserToken.test_authenticate_user_role(response.data["user_id"], response.data.access_token)
              .then(function (_response) {

                if(isUserAdmin(_response)) {
                  UserToken.authenticate_user(response.data);
                  logger.info("User authenticated successfully.");
                  $state.go('scheduler_admin');
                }
              },error);
         }
       },error);

      /**
       * Show error message to user
       * @param err
         */
      function error(err){
         vm.error_message = "Unauthorized: You don't have access to get-Talent";
        logger.error(err);
      }
    };

    activate();

    function activate() {

    }
  }
})();
