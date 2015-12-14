$(document).ready(function() {
    console.log("Don't forget to remove this prior to launch, all final UI work to be integrated into the current setup");
});

App.View.Dashboard = function () {
    var areaGraphData = [[{ date: '07-01-15', data: 90 }, { date: '07-15-15', data: 23 }, { date: '08-01-15', data: 71 }, { date: '08-15-15', data: 51 }, { date: '09-01-15', data: 112 }, { date: '09-15-15', data: 39 }, { date: '10-01-15', data: 45 }, { date: '10-15-15', data: 8 }, { date: '11-01-15', data: 88 }], [{ date: '07-01-15', data: 30 }, { date: '07-15-15', data: 133 }, { date: '08-01-15', data: 21 }, { date: '08-15-15', data: 79 }, { date: '09-01-15', data: 52 }, { date: '09-15-15', data: 119 }, { date: '10-01-15', data: 15 }, { date: '10-15-15', data: 80 }, { date: '11-01-15', data: 14 }]];

    var lineGraphData = [{ date: '10-07-15', data: 10 }, { date: '10-08-15', data: 11 }, { date: '10-09-15', data: 13 }, { date: '10-10-15', data: 15 }, { date: '10-11-15', data: 10 }, { date: '10-12-15', data: 7 }, { date: '10-13-15', data: 8 }, { date: '10-14-15', data: 10 }, { date: '10-15-15', data: 10 }, { date: '10-16-15', data: 14 }, { date: '10-17-15', data: 15 }, { date: '10-18-15', data: 10 }];

    var circleGraphData = 33;

    App.Module.AreaGraph.init($('.js-graph--total-candidates'), areaGraphData);
    App.Module.LineGraph.init($('.js-graph--new-candidates'), lineGraphData);
    App.Module.CircleGraph.init($('.js-graph--pipeline-engagement'), circleGraphData);
};
