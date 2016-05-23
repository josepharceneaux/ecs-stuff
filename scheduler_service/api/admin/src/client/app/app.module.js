(function() {
  'use strict';

  angular.module('app', [
    'app.core',
    'app.widgets',
    'app.login',
    'app.scheduler_admin',
    'app.dashboard',
    'app.layout'
  ])
  //  .config(function($locationProvider) {
  //  $locationProvider.html5Mode(false);
  //  $locationProvider.hashPrefix('!');
  //})
  ;

})();
