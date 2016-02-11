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

    configFunction.$inject = ['$provide', '$compileProvider', '$httpProvider', '$logProvider', 'exceptionHandlerProvider',
        'OAuthProvider', 'OAuthTokenProvider', 'pickADateProvider', 'pickATimeProvider',
        'tagsInputConfigProvider', 'authInfo', '$uibTooltipProvider', '$mdThemingProvider',
        'toastrConfig', '$breadcrumbProvider', 'areaGraphConfigProvider'];

    /* @ngInject */
    function configFunction($provide, $compileProvider, $httpProvider, $logProvider, exceptionHandlerProvider,
                            OAuthProvider, OAuthTokenProvider, pickADateProvider, pickATimeProvider,
                            tagsInputConfigProvider, authInfo, $uibTooltipProvider, $mdThemingProvider,
                            toastrConfig, $breadcrumbProvider, areaGraphConfigProvider) {

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

        $httpProvider.interceptors.push('authorizationInterceptor');

        // specify primary color, all
        // other color intentions will be inherited
        // from default
        $mdThemingProvider
            .theme('altTheme')
            .primaryPalette('purple');

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
            placement: 'auto right'
        });

        angular.extend(toastrConfig, {
            // container config
            autoDismiss: false,
            containerId: 'toast-container',
            maxOpened: 1,
            newestOnTop: true,
            positionClass: 'toast-bottom-right',
            preventDuplicates: false,
            preventOpenDuplicates: false,
            target: 'body',

            // toast config
            allowHtml: true,
            closeButton: true,
            closeHtml: '<button>Dismiss</button>',
            extendedTimeOut: 1000,
            iconClasses: {
                error: 'toast-error',
                info: 'toast-info',
                success: 'toast-success',
                warning: 'toast-warning'
            },
            messageClass: 'toast-message',
            onHidden: null,
            onShown: null,
            onTap: null,
            progressBar: true,
            tapToDismiss: false,
            templates: {
                toast: 'directives/toast/toast.html',
                progressbar: 'directives/progressbar/progressbar.html'
            },
            timeOut: false,
            titleClass: 'toast-title',
            toastClass: 'toast'
        });

        $provide.decorator('hljsDirective', HljsDecorator);

        $breadcrumbProvider.setOptions({
            templateUrl: 'core/modules/breadcrumb/breadcrumb.html'
        });

        areaGraphConfigProvider.setOptions({
            colors: {}
        });
    }

    // Decorate the hjls directive so that we can assign classes to the <code> element
    HljsDecorator.$inject = ['$delegate'];

    /* @ngInject */
    function HljsDecorator($delegate) {
        var directive = $delegate[0];
        var compile = directive.compile;
        directive.compile = function newCompile(tElement, tAttrs, transclude) {
            var link = compile.apply(this, arguments);
            var isLinkObject = typeof link === 'object';
            var newPostLink = function ($scope, $element, $attrs, $controllerDirective, $transcludeFunc) {
                var $codeEl;
                if (isLinkObject) {
                    link.post.apply(this, arguments);
                } else {
                    link.apply(this, arguments);
                }
                if ($attrs.codeClass) {
                    $codeEl = $element.find('code');
                    $codeEl.addClass($attrs.codeClass);
                }
            };
            if (isLinkObject) {
                newPostLink = {
                    pre: link.pre,
                    post: newPostLink
                }
            }
            return newPostLink;
        };
        return $delegate;
    }
})();
