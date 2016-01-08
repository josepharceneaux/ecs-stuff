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

    configFunction.$inject = ['$provide', '$compileProvider', '$logProvider', 'exceptionHandlerProvider',
        'OAuthProvider', 'OAuthTokenProvider', 'pickADateProvider', 'pickATimeProvider',
        'tagsInputConfigProvider', 'authInfo', 'tooltipsConfProvider'];

    /* @ngInject */
    function configFunction($provide, $compileProvider, $logProvider, exceptionHandlerProvider,
                            OAuthProvider, OAuthTokenProvider, pickADateProvider, pickATimeProvider,
                            tagsInputConfigProvider, authInfo, tooltipsConfProvider) {

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

        $provide.decorator('tooltipsDirective', tooltipsDecorator);

        tooltipsConfProvider.configure({
            smart: true
        });

        // The following decorator sets tooltips default appendToBody value to 'true'.
        // The third party plugin doesn't allow configuring this default through its provider, the traditional method.
        tooltipsDecorator.$inject = ['$delegate', 'tooltipsConf'];

        /* @ngInject */
        function tooltipsDecorator($delegate, tooltipsConf) {
            var directive = $delegate[0];

            tooltipsConf.appendToBody = true;

            directive.compile = function () {
                return function ($scope, $element, $attrs, $controllerDirective, $transcludeFunc) {
                    $attrs.tooltipAppendToBody = $attrs.tooltipAppendToBody || (tooltipsConf.appendToBody ? 'true' : 'false');
                    directive.link.apply(this, arguments);
                };
            }
            return $delegate;
        } // End tooltipsConf override
    }
})();
