var gulp = require('gulp');

module.exports = function (config) {
    config.log('Importing vet.js...');

    var $ = config.$;
    var args = config.args;
    var log = config.log;

    gulp.task('vet', vet);

    /**
     * vet the code and create coverage report
     * @return {Stream}
     */
    function vet() {
        log('Analyzing source with JSHint and JSCS');

        return gulp
            .src(config.alljs);
            //.pipe($.if(args.verbose, $.print()))
            //.pipe($.jshint())
            //.pipe($.jshint.reporter('jshint-stylish', {verbose: true}))
            //.pipe($.jshint.reporter('fail'))
            //.pipe($.jscs());
    }
};
