(function () {
    'use strict';

    var core = angular.module('app.core');

    // Application configuration values
    var config = {
        appErrorPrefix: '[GetTalent Dashboard Error] ',
        appTitle: 'GetTalent Dashboard'
    };

    core.value('config', config);

    // Configure the app
    core.config(configFunction);

    configFunction.$inject = ['$compileProvider', '$logProvider', 'exceptionHandlerProvider',
        'OAuthProvider', 'OAuthTokenProvider', 'pickADateProvider', 'pickATimeProvider',
        'tagsInputConfigProvider', 'authInfo', '$uibTooltipProvider'];

    /* @ngInject */
    function configFunction($compileProvider, $logProvider, exceptionHandlerProvider,
                            OAuthProvider, OAuthTokenProvider, pickADateProvider, pickATimeProvider,
                            tagsInputConfigProvider, authInfo, $uibTooltipProvider) {

        // During development, you may want to set debugInfoEnabled to true. This is required for tools like
        // Protractor, Batarang and ng-inspector to work correctly. However do not check in this change.
        // This flag must be set to false in production for a significant performance boost.
        $compileProvider.debugInfoEnabled(false);

        // turn debugging off/on (no info or warn)
        if ($logProvider.debugEnabled) {
            $logProvider.debugEnabled(true);
        }

        exceptionHandlerProvider.configure(config.appErrorPrefix);

        OAuthProvider.configure({
            baseUrl: authInfo.baseUrl,
            clientId: authInfo.clientId,
            clientSecret: authInfo.clientSecret,
            grantPath: authInfo.grantPath
        });

        OAuthTokenProvider.configure({
            name: 'gt_token',
            options: {
                secure: false
            }
        });

        pickADateProvider.setOptions({
            today: '',
            format: 'mmmm dd, yyyy'
        });

        pickATimeProvider.setOptions({
            today: ''
        });

        tagsInputConfigProvider
            .setDefaults('tagsInput', {
                minLength: 1,
                replaceSpacesWithDashes: false
            })
            .setTextAutosizeThreshold(13.6);

        $uibTooltipProvider.options({
            appendToBody: true,
            placement: 'auto'
        });
    }
})();
