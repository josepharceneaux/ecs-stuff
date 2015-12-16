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

        var GRADIENT_START = '#0096c4';
        var GRADIENT_END = '#78cbe4';

        // -----
        // Utils
        // -----

        var d3ParseDate = d3.time.format('%m-%d-%Y').parse;
        var d3BisectDate = d3.bisector(function (d) {
            return d3ParseDate(d.date);
        }).left;

        var hideAll = function hideAll() {
            var arr = arguments.length <= 0 || arguments[0] === undefined ? array() : arguments[0];

            for (var _i = 0; _i < arr.length; _i++) {
                arr[_i].style('opacity', 0);
            }
        };

        // -----
        // Draw
        // -----

        var draw = {
            canvas: function canvas($chart) {
                var width = $chart.width();

                module.chart.$canvas = d3.select($chart.get(0)).append('svg');
                module.chart.$inner = module.chart.$canvas.append('g');

                module.chart.$canvas.attr('class', 'areaGraph__canvas');
                module.chart.$inner.attr('class', 'areaGraph__canvas__inner');

                module.chart.width = width;
                module.chart.height = module.chart.width * .315;

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

                module.chart.$xAxis.attr('class', 'areaGraph__xAxis');
            },
            yAxis: function yAxis(data) {
                module.chart.y = d3.scale.linear();

                module.chart.y.range([module.chart.height, 0]);
                module.chart.y.domain([-30, d3.max(data, function (d) {
                    return d.data + d.data * 0.33;
                })]);
            },
            xPoints: function xPoints(data) {
                for (var _i2 = 0; _i2 < data.length; _i2++) {
                    if (_i2 === 0 || _i2 === data.length - 1) continue;

                    module.chart.$xAxis.append('text').attr({
                        'x': module.chart.x(d3ParseDate(data[_i2].date)),
                        'y': module.chart.height - MARGIN,
                        'text-anchor': 'middle',
                        'fill': '#ffffff',
                        'class': 'areaGraph__xAxis__label'
                    }).text(moment(data[_i2].date).format('M/D/YYYY'));

                    module.chart.$xAxis.append('rect').attr({
                        'class': 'areaGraph__notch',
                        x: module.chart.x(d3ParseDate(data[_i2].date)) - 2,
                        y: module.chart.height - MARGIN - 40,
                        width: 3,
                        height: 15
                    });
                }
            },
            xLine: function xLine() {
                module.chart.$xLine = module.chart.$xAxis.append('line');

                module.chart.$xLine.attr('class', 'areaGraph__xAxis__line');

                module.chart.$xLine.attr('x2', module.chart.width);
                module.chart.$xLine.attr('y1', module.chart.height - MARGIN - 20);
                module.chart.$xLine.attr('y2', module.chart.height - MARGIN - 20);
            },
            area: function area(data) {
                var altStyle = arguments.length <= 1 || arguments[1] === undefined ? false : arguments[1];

                var area = d3.svg.area();

                area.x(function (d) {
                    return module.chart.x(d3ParseDate(d.date));
                });
                area.y0(module.chart.height);
                area.y1(function (d) {
                    return module.chart.y(d.data);
                });

                module.chart.$area = module.chart.$inner.append('path');
                module.chart.$area.attr('class', 'areaGraph__area' + (altStyle ? '--alt' : ''));

                module.chart.$area.datum(data);
                module.chart.$area.attr('d', area);
            },
            linePoints: function linePoints(data) {
                module.chart.$pointGroup = module.chart.$pointGroup || [];
                module.chart.$points = module.chart.$points || [];

                var pointGroup = [];

                var $group = undefined;
                var $point = undefined;
                var $pg = undefined;
                var $bar = undefined;
                var $tooltip = undefined;

                $pg = module.chart.$inner.append('g');
                $pg.attr('class', 'areaGraph__pointGroup');

                var _loop = function (_i3) {
                    if (!data.hasOwnProperty(_i3)) return 'continue';

                    // Append the point contianer

                    $group = $pg.append('g');
                    $group.attr('class', 'areaGraph__point');

                    // Append the point (circle)

                    $point = $group.append('circle');

                    $point.attr('class', 'areaGraph__point__circle');
                    $point.attr('cx', function (d) {
                        return module.chart.x(d3ParseDate(data[_i3].date));
                    });
                    $point.attr('cy', function (d) {
                        return module.chart.y(data[_i3].data);
                    });
                    $point.attr('r', POINT_RADIUS);

                    // Append the bar

                    $bar = $group.append('line');

                    $bar.attr('class', 'areaGraph__point__bar');
                    $bar.attr('x1', function (d) {
                        return module.chart.x(d3ParseDate(data[_i3].date));
                    });
                    $bar.attr('x2', function (d) {
                        return module.chart.x(d3ParseDate(data[_i3].date));
                    });
                    $bar.attr('y1', function (d) {
                        return module.chart.height;
                    });
                    $bar.attr('y2', function (d) {
                        return module.chart.y(data[_i3].data) + 6;
                    });

                    // Append the tooltip

                    $tooltip = $group.append('text');

                    $tooltip.attr('class', 'areaGraph__point__text');
                    $tooltip.attr('transform', function (d) {
                        return 'translate(' + module.chart.x(d3ParseDate(data[_i3].date)) + ',' + module.chart.y(data[_i3].data) + ')';
                    });
                    $tooltip.attr({ dx: '.55em', dy: '.55em' });
                    $tooltip.text(function (d) {
                        return '+ ' + data[_i3].data;
                    });

                    // Add this group to the main group array

                    module.chart.$points.push($group);
                    pointGroup.push($group);
                };

                for (var _i3 in data) {
                    var _ret = _loop(_i3);

                    if (_ret === 'continue') continue;
                }

                module.chart.$pointGroup.push(pointGroup);
            },
            gradients: function gradients() {
                module.chart.$gradients = module.chart.$canvas.append('g');
                module.chart.$gradient1 = module.chart.$gradients.append('linearGradient');

                module.chart.$gradients.attr('class', 'areaGraph__gradients');

                // White Gradient

                module.chart.$gradient1.attr('id', 'areaGraph__gradient');
                module.chart.$gradient1.attr('gradientUnits', 'userSpaceOnUse');

                module.chart.$gradient1.append('stop').attr('offset', '0').attr('stop-color', GRADIENT_START);

                module.chart.$gradient1.append('stop').attr('offset', '0.5').attr('stop-color', GRADIENT_END);
            },
            mouseEvents: function mouseEvents(data) {
                module.chart.$inner.on('mousemove', function () {
                    var x0 = module.chart.x.invert(d3.mouse(this)[0]);
                    var i = d3BisectDate(data, x0);

                    var $point1 = module.chart.$pointGroup[0][i];
                    var $point2 = module.chart.$pointGroup[1][i];

                    hideAll(module.chart.$points);

                    $point1.style('opacity', 1);
                    $point2.style('opacity', 1);
                });

                module.chart.$inner.on('mouseleave', function () {
                    return hideAll(module.chart.$points);
                });
            }
        };

        var drawChart = function drawChart($chart, data) {
            if (module.chart.$canvas) {
                module.chart.$canvas.remove();
            }

            draw.canvas($chart);
            draw.gradients();

            if (data[0]) {
                draw.xAxis(data[0]);
                draw.yAxis(data[0]);
                draw.xPoints(data[0]);

                draw.area(data[0]);
                draw.linePoints(data[0]);
                draw.mouseEvents(data[0]);
            }

            if (data[1]) {
                draw.area(data[1], true);
                draw.linePoints(data[1]);
                draw.mouseEvents(data[1]);
            }
        };

        // -----
        // Public Methods
        // -----

        function init($chart, data) {
            drawChart($chart, data);
            $(window).on('resize', function () {
                return drawChart($chart, data);
            });
        }

        init(elem, scope.data);

    }
})();
