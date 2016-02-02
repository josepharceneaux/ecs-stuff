// -------------------------------------
//   Watch div width & height change
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtResize', directiveFunction)        

    // ----- directiveFunction -----
    directiveFunction.$inject = ['$interval'];

    /* @ngInject */
    function directiveFunction($interval) {

        var directive = {
            restrict: 'A',
            scope: {
                onResize: '&'
            },
            link: linkFunction
        };

        return directive;

        function linkFunction(scope, elem, attrs, ctrls) {
            init();

            ///////////////

            function init() {

                // Use $interval as $watch is working very slowly                
                var curWidth = elem.width();

                var stop = $interval(function() {

                    if (curWidth !== elem.width()) {
                        
                        curWidth = elem.width();                        

                        scope.onResize();
                        
                    }

                }, 100);

                scope.$on('$destroy', function () {
                    
                    if (angular.isDefined(stop)) {

                        $interval.cancel(stop);
                        stop = undefined;

                    }

                });

                // $watch is working very slowly, 
                // causing calling the onResize handler delayed
                
                /* scope.$watch(function () {
                    
                    return JSON.stringify({
                        width: elem.width(),
                        heigth: elem.height()
                    });

                }, function (newValue, oldValue) {                    

                    if (newValue !== oldValue) {

                        scope.onResize();

                    }
                }); */
            }
        }
    }
})();
