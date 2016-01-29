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
        var angle = parseFloat(attrs.angle) || 75;
        var value = attrs.value || 0;
        var svg;
        var arc;
        var innerCircle;
        var label;

        svg = d3.select($(elem).children()[0])
            .append('svg')
            .attr("width", '360')
            .attr("height", '360px')
            .append("g")
            .attr("transform", "translate(180,150)");


        arc = d3.svg.arc()
            .innerRadius(85)
            .outerRadius(115)
            .startAngle(0)
            .endAngle((angle / 100 ) * 2 * Math.PI);

        innerCircle = d3.svg.arc()
            .innerRadius(0)
            .outerRadius(80)
            .startAngle(0)
            .endAngle(2 * Math.PI);


        svg.append("path")
            .attr("class", "path path--background")
            .attr("d", arc);

        svg.append("path")
            .attr("class", "path path--foreground")
            .attr("d", innerCircle);

        label = svg.append("text")
            .attr("class", "label")
            .attr("dy", ".25em")
            .attr("dx", ".2em")
            .text(angle + '%');

        svg.append("text")
            .attr("class", "inner-label")
            .attr("dy", "2em")
            .attr("dx", ".1em")
            .text('(' + value + ')');

        svg.append("text")
            .attr("width", "200")
            .attr("class", "legend label")
            .attr("height", "12")
            .attr("x", '-43')
            .attr("y", '10.3em')
            .text("Candidates Used In [segment]");

        svg.append("rect")
            .attr("class", "legend off-white")
            .attr("width", "12")
            .attr("height", "12")
            .attr("x", '-165')
            .attr("y", '9em');

        svg.append("text")
            .attr("width", "200")
            .attr("class", "legend label")
            .attr("height", "12")
            .attr("x", '-30')
            .attr("y", '11.7em')
            .text("Candidates Available from [Parent]");

        svg.append("rect")
            .attr("class", "legend purple")
            .attr("width", "12")
            .attr("height", "12")
            .attr("x", '-165')
            .attr("y", '10.3em');
    }

})();
