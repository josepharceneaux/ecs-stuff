// -------------------------------------
//   Bar Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtBarGraph', directiveFunction)
        .controller('BarGraphController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AE',
            require: ['gtBarGraph'],
            scope: {
                data: '=?',
                options: '=?'
            },
            controller: 'BarGraphController',
            controllerAs: 'barGraph',
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
        var barHeight = parseInt(attrs.barHeight) || 40;
        var barSpacing = parseInt(attrs.barSpacing) || 10;

        var svg = d3.select($(elem).children()[0])
            .append('svg')
            .attr("width", '100%');

        var xScale = d3.scale.linear().domain([0, 100]).range([0, '100%']);
        var height;

        scope.data = [
            {
                title: 'Android',
                value: '2000',
                percentage: '95'
            },
            {
                title: 'App Development',
                value: '200',
                percentage: '90'
            },
            {
                title: 'iOS',
                value: '1600',
                percentage: '80'
            },
            {
                title: 'C++',
                value: '900',
                percentage: '62'
            },
            {
                title: 'Java',
                value: '800',
                percentage: '55'
            },
            {
                title: 'UI',
                value: '800',
                percentage: '35'
            }
        ];

        height = scope.data.length * (barHeight + barSpacing);

        svg.attr('height', height);

        svg.selectAll('rect')
            .data(scope.data).enter()
            .append('rect')
            .attr('height', barHeight)
            .attr('width', 0)
            .attr('y', function(d,i) {
              return i * (barHeight) + (i + 1) * barSpacing;
            })
            .attr('fill', '#d2d7d3')
            .transition()
            .duration(1000)
            .attr('width', function(d) {
                return xScale(d.percentage);
            });

        svg.selectAll('text')
            .data(scope.data).enter()
            .append('text')
            .attr('x', 0)
            .attr("dx", -35)
            .attr("dy", ".35em")
            .attr('y', function(d,i) {
              return i * (barHeight) + (i + 1) * barSpacing + (barHeight/2);
            })
            .attr('fill', '#fff')
            .transition()
            .duration(1000)
            .attr('x', function(d) {
                return xScale(d.percentage);
            })
            .text(function(d) {
                return d.percentage + '%';
            });

        scope.data.forEach(function(d, i){
            svg.append('text')
                .attr('y', i * (barHeight) + (i + 1) * barSpacing - 6)
                .attr('fill', '#777')
                .text(d.title);
                //.text(d.title + ' (' + d.value + ')');
        });
    }

})();
