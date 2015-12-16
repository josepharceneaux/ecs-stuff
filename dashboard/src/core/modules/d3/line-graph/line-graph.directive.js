// -------------------------------------
//   Line Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtLineGraph', directiveFunction)
        .controller('LineGraphController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AE',
            require: ['gtLineGraph'],
            scope: {
                data: '=',
                options: '='
            },
            controller: 'LineGraphController',
            controllerAs: 'lineGraph',
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
        var MARGIN = 30;
        var POINT_RADIUS = 6;

        // -----
        // Utils
        // -----

        var d3ParseDate = d3.time.format('%m-%d-%Y').parse;

        // -----
        // Private Functions
        // -----

        var showPoint = function showPoint(d) {
            var $point = d3.select(this);

            $point.attr('r', POINT_RADIUS * 1.05);
            $point.attr('stroke-width', POINT_RADIUS);
        };

        var draw = {
            canvas: function canvas($chart) {
                var width = $chart.width();

                module.chart.$canvas = d3.select($chart.get(0)).append('svg');
                module.chart.$inner = module.chart.$canvas.append('g');

                module.chart.$canvas.attr('class', 'lineGraph__canvas');
                module.chart.$inner.attr('class', 'lineGraph__canvas__inner');

                module.chart.width = width - MARGIN * 2;
                module.chart.height = module.chart.width * .75;

                // Enforce max height
                if (module.chart.height > 175) module.chart.height = 175;

                // Set width/height of the canvas
                module.chart.$canvas.attr('width', module.chart.width).attr('height', module.chart.height);
            },
            xAxis: function xAxis(data) {
                module.chart.x = d3.time.scale();
                module.chart.$xAxis = module.chart.$canvas.append('g');

                module.chart.x.range([0, module.chart.width]);
                module.chart.x.domain(d3.extent(data, function (d) {
                    return d3ParseDate(d.date);
                }));

                module.chart.$xAxis.attr('class', 'lineGraph__xAxis');
            },
            yAxis: function yAxis(data) {
                module.chart.y = d3.scale.linear();

                module.chart.y.range([module.chart.height, 0]);
                module.chart.y.domain([0, d3.max(data, function (d) {
                    return d.data + d.data * 0.33;
                })]);
            },
            xPoints: function xPoints(data) {
                var tickScale = module.chart.size / data.length;

                for (var _i4 in data) {
                    if (!data.hasOwnProperty(_i4) || _i4 % 2 !== 1) continue;

                    module.chart.$xAxis.append('text').attr({
                        'x': module.chart.x(d3ParseDate(data[_i4].date)),
                        'y': module.chart.height - MARGIN,
                        'text-anchor': 'middle',
                        'fill': '#bfbfbf'
                    }).text(moment(data[_i4].date).format('D')).style('font-size', '.9em');
                }
            },
            xLine: function xLine() {
                module.chart.$xLine = module.chart.$xAxis.append('line');

                module.chart.$xLine.attr('class', 'lineGraph__xAxis__line');

                module.chart.$xLine.attr('x2', module.chart.width);
                module.chart.$xLine.attr('y1', module.chart.height - MARGIN - 20);
                module.chart.$xLine.attr('y2', module.chart.height - MARGIN - 20);
            },
            line: function line(data) {
                var lineStart = d3.svg.line();
                var lineEnd = d3.svg.line();

                lineStart.x(function (d) {
                    return module.chart.x(d3ParseDate(d.date));
                });
                lineStart.y(function (d) {
                    return module.chart.y(0);
                });

                lineEnd.x(function (d) {
                    return module.chart.x(d3ParseDate(d.date));
                });
                lineEnd.y(function (d) {
                    return module.chart.y(d.data);
                });

                module.chart.$line = module.chart.$inner.append('path');

                module.chart.$line.attr('class', 'lineGraph__line');

                module.chart.$line.attr('d', lineStart(data));
                module.chart.$line.transition().duration(500);
                module.chart.$line.attr('d', lineEnd(data));
            },
            linePoints: function linePoints(data) {
                module.chart.$pointGroup = module.chart.$inner.append('g');
                module.chart.$points = module.chart.$pointGroup.selectAll('circle').data(data).enter().append('circle');

                module.chart.$pointGroup.attr('class', 'lineGraph__pointGroup');

                module.chart.$points.attr('class', 'lineGraph__point');
                module.chart.$points.attr('cx', function (d) {
                    return module.chart.x(d3ParseDate(d.date));
                });
                module.chart.$points.attr('cy', function (d) {
                    return module.chart.y(0);
                });
                module.chart.$points.attr('cy', function (d) {
                    return module.chart.y(d.data);
                });
                module.chart.$points.attr('r', POINT_RADIUS);

                module.chart.$points.on('mouseover', showPoint);
            },
            lineMarker: function lineMarker() {
                module.chart.$lineBar = module.chart.$inner.append('line');

                module.chart.$lineBar.attr('class', 'lineGraph__marker');
            }
        };

        var drawChart = function drawChart($chart, data) {
            if (module.chart.$canvas) {
                module.chart.$canvas.remove();
            }

            draw.canvas($chart);
            draw.xAxis(data);
            draw.yAxis(data);
            draw.xLine();
            draw.xPoints(data);
            draw.line(data);
            draw.linePoints(data);
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
