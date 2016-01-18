(function() {
    'use strict';

    angular.module('app', [
        // Common (everybody has access to these)
        'app.core',

        // Features (listed alphabetically)
        'app.admin',
        'app.approot',
        'app.campaigns',
        'app.candidates',
        'app.dashboard',
        'app.footer',
        'app.forgotPassword',
        'app.login',
        'app.main',
        'app.pipelines',
        'app.search',
        'app.sidenav',
        'app.smartLists',
        'app.styleguide',
        'app.talentPools',
        'app.topnav'
    ]);
    angular.module('myApp', ['ngMaterial'])
        .config(function($mdThemingProvider) {
            $mdThemingProvider.theme('altTheme')
                .primaryPalette('purple') // specify primary color, all
            // other color intentions will be inherited
            // from default
        });
})();



