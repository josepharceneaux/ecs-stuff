// -------------------------------------
//   Float Labels
//   -> If an input has a label, then check to see if it has a value.
//      If so, then float the label above the input
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtFloatLabel', directiveFunction)
        .controller('FloatLabelController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AC',
            require: ['gtFloatLabel', '?ngModel'],
            scope: {
            },
            controller: 'FloatLabelController',
            controllerAs: 'vm',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        //var vm = this;
    }

    // ----- ControllerFunction -----
    linkFunction.$inject = [];

    /* @ngInject */
    function linkFunction(scope, elem, attrs, ctrls) {
        var ngModel = ctrls[1];
        var parents = elem.parents('.form__col');
        var unregister;

        init();

        ///////////////

        function init() {
            if (ngModel) {

                // Element and model value isn't initialized yet,
                // watch value until it changes once.
                unregister = scope.$watch(function () {
                    return ngModel.$viewValue;
                }, valueChangeListener);

                // If input has any validators (e.g. ngPattern, type="email"),
                // viewChangeListeners will never fire, so also add a listener
                // for parsing.
                ngModel.$parsers.push(checkInput);
                ngModel.$viewChangeListeners.push(checkInput);
            } else {

                // Element and model value isn't initialized yet,
                // watch value until it changes once.
                unregister = scope.$watch(function () {
                    return elem.val();
                }, valueChangeListener);

                elem.on('keyup change', function () {
                    checkInput(elem.val());
                });
            }
        }

        function valueChangeListener(value, oldValue) {
            if (value !== oldValue) {
                unregister();
            }
            checkInput(value);
        }

        function checkInput(inputValue) {
            if (inputValue) {
                parents.addClass('form__col--has-value');
            } else {
                parents.removeClass('form__col--has-value');
            }
        }
    }
})();
