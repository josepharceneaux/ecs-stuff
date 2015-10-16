(function() {
    'use strict';

    angular.module('app', [
        // Common (everybody has access to these)
        'app.core',

        // Features (listed alphabetically)
        'app.admin',
        'app.approot',
        'app.campaigns',
        'app.dashboard',
        'app.footer',
        'app.help',
        'app.login',
        'app.pipeline',
        'app.sidenav',
        'app.topnav'
    ]);
})();
