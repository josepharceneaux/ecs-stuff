var gulp = require('gulp');

module.exports = function (config) {
    config.log('Importing config.js...');

    gulp.task('config', function () {
        var env = process.env.GT_NODE_ENV || 'development';

        return gulp
            .src(config.sourceDir + 'config.json')
            .pipe(config.$.ngConfig('app.config', {
                environment: env,
                wrap: true
            }))
            .pipe(gulp.dest(config.tempDir));
    });
};
