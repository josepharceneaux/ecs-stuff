// -------------------------------------
//   Shake div
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtShakeDiv', directiveFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = ['$animate'];

    /* @ngInject */
    function directiveFunction($animate) {

        var directive = {
            scope: {
                shakeTrigger: '='
            },            
            link: linkFunction
        };

        return directive;

        function linkFunction(scope, element, attrs) {
            
            scope.$watch('shakeTrigger', function(newValue, oldValue) {

                console.log('shakeTrigger Change', newValue);

                if (newValue === oldValue || newValue === false) {
                    
                    return;

                }

                $animate.addClass(element, 'shake').then(function() {

                    console.log('$animate.addClass callback');

                    $animate.removeClass(element, 'shake');

                    scope.shakeTrigger = false;

                });
            });
        }
    }
        
})();
