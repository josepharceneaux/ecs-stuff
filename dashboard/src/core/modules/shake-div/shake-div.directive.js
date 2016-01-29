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
                error: '='
            },            
            link: linkFunction
        };

        return directive;

        function linkFunction(scope, element, attrs) {
            
            scope.$watch('error', function(newValue, oldValue) {

                if (newValue === oldValue) return;

                console.log('change');

                $animate.addClass(element, 'shake', function() {
                    $animate.removeClass(element, 'shake');
                });
            });
        }
    }
        
})();
