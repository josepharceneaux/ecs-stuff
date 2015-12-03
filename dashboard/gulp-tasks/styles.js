var gulp = require('gulp');
var watch = require('gulp-watch');

module.exports = function (config) {
    config.log('Importing styles.js...');

    var $ = config.$;

    gulp.task('styles', ['clean-styles'], function () {
        config.log('Compiling Sass --> CSS');

        return gulp
            .src(config.sourceDir + 'app.scss')
            .pipe($.plumber()) // exit gracefully if something fails after this
            .pipe($.sourcemaps.init())
            .pipe($.sass({
                outputStyle: 'compressed'
            }))
            .pipe($.autoprefixer({
                browsers: [
                    'last 2 version',
                    'safari 5',
                    'ie 8',
                    'ie 9',
                    'opera 12.1',
                    'ios 6',
                    'android 4'
                ]
            }))
            .pipe($.sourcemaps.write())
            .pipe(gulp.dest(config.tempDir));
    });

    gulp.task('sass-watcher', function () {
        watch(config.sass, ['styles']);
    });
};
