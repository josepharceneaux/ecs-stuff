// -------------------------------------
//   Circle Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtCircleGraph', directiveFunction)
        .controller('CircleGraphController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AE',
            require: ['gtCircleGraph'],
            scope: {
                data: '=',
                options: '='
            },
            controller: 'CircleGraphController',
            controllerAs: 'circleGraph',
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

    function linkFunction(scope, elem, attrs, ctrls) {

        var module = { chart: {} };

        // -----
        // Constants
        // -----

        var MAX_WIDTH = 200;

        // -----
        // Draw
        // -----

        var draw = {
            canvas: function canvas($element) {
                var height = width;
                var canvas = d3.select($element.get(0)).append('svg').attr('class', 'circleGraph__canvas');
                var inner = canvas.append('g').attr('class', 'circleGraph__canvas__inner');
                var width = $element.width();

                module.chart._size = width > MAX_WIDTH ? MAX_WIDTH : width;

                // Set width/height of the canvas
                canvas.attr('width', module.chart._size).attr('height', module.chart._size);

                // Set width/height of inner container
                inner.attr('transform', 'translate(' + module.chart._size / 2 + ',' + module.chart._size / 2 + ')');

                return canvas;
            },
            meter: function meter(Canvas) {
                var meter = Canvas.select('.circleGraph__canvas__inner').append('g').attr('class', 'circleGraph__meter');
                var circle = meter.append('circle').attr('class', 'circleGraph__circle');

                circle.attr({
                    'cx': '0',
                    'cy': '0',
                    'r': '50%'
                });

                return meter;
            },
            progress: function progress(Meter) {
                var progress = Meter.append('path').attr('class', 'circleGraph__progress');
                var twoPi = 2 * Math.PI;
                var arc = d3.svg.arc().startAngle(0).innerRadius(module.chart._size / 2).outerRadius(module.chart._size / 2);

                return progress;
            },
            text: function text(Meter) {
                var text = Meter.append('text').attr('class', 'circleGraph__text');

                text.attr({
                    'text-anchor': 'middle',
                    'dy': '.35em'
                });

                return text;
            }
        };

        var drawChart = function drawChart($chart, data) {
            if (module.chart.canvas) {
                module.chart.canvas.remove();
            }

            module.chart.canvas = draw.canvas($chart);
            module.chart.meter = draw.meter(module.chart.canvas);
            module.chart.progress = draw.progress(module.chart.meter);
            module.chart.text = draw.text(module.chart.meter);

            displayData(data);
        };

        var displayData = function displayData() {
            var percentage = arguments.length <= 0 || arguments[0] === undefined ? 0 : arguments[0];

            var twoPi = 2 * Math.PI;
            var arc = d3.svg.arc().startAngle(0).innerRadius(module.chart._size / 2).outerRadius(module.chart._size / 2);

            module.chart.text.text(d3.format('.0%')((percentage / 100).toString()));
            module.chart.progress.attr('d', arc.endAngle(twoPi * (percentage / 100) * -1));
        };

        // -----
        // Public Methods
        // -----

        function init($chart, data) {
            drawChart($chart, data);
            $(window).on('resize', function () {
                return drawChart($chart, data);
            });
        };

        init(elem, scope.data);

    }
})();
