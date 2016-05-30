(function() {
  'use strict';

  angular
    .module('app.login')
    .controller('LoginController', LoginController);

  LoginController.$inject = ['logger', '$state', 'UserToken', '$http', 'api_info'];
  /* @ngInject */
  function LoginController(logger, $state, UserToken, $http, api_info) {
    var vm = this;
    vm.title = 'Login';

    if(UserToken.is_authenticated_user())
      $state.go('scheduler_admin');

    vm.login = function () {

       $http({
         method: 'POST',
         url: api_info.apiInfo.authService.grantPath,

         headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
         },
         data: $.param({
           username: vm.email,
           password: vm.password,
           grant_type: "password",
           "client_id": "KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z",
           "client_secret": "DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z"
         })
       }).then(function (response) {
         if("access_token" in response.data){
           UserToken.authenticate_user(response.data);
           $state.go('scheduler_admin');
         }
       },function (err) {
         console.log(err);
         if(err.status == 401)
            vm.error_message = "Unauthorized Access: You don't have access to getTalent"
       });
    };

    activate();

    function activate() {

    }
  }
})();
