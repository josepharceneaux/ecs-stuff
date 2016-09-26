(function () {
  'use strict';

  angular
    .module('app.core')
    .run(appRun);

  appRun.$inject = ['apiInfo'];
  /* @ngInject */
  function appRun(apiInfo) {

     apiInfo.readApiInfo();
  }

})();
