var gulp = require('gulp');
var watch = require('gulp-watch');
var runSequence = require('run-sequence').use(gulp);

module.exports = function (config) {
    config.log('Importing icon-fonts.js...');

    var $ = config.$;

    var iconSrc = config.sourceDir + 'core/icon-font/icon-src/*.svg';
    var fontName = 'gettalent-icons';
    var cacheName = 'icon-font';

    gulp.task('icon-font', function (cb) {
        var icons = [];
        var changedIcons = [];
        var cachedIcons = [];

        gulp.src(iconSrc)
            .on('data', function (data) {
                icons.push(data);
            })
            .pipe($.cached(cacheName))
            .on('data', function (data) {
                changedIcons.push(data);
            })
            .pipe($.remember(cacheName))
            .on('data', function (data) {
                cachedIcons.push(data);
            })
            .on('end', function () {
                if (changedIcons.length > 0 || icons.length < cachedIcons.length) {
                    runSequence('build-icon-font', function () {
                        cb();
                    });
                } else {
                    cb();
                }
            });
    });

    gulp.task('build-icon-font', ['clean-icon-font-cache'], function (cb) {
        gulp
            .src(iconSrc)
            .pipe($.cached(cacheName))
            .pipe($.remember(cacheName))
            .pipe($.iconfont({
                fontName           : fontName,
                fontHeight         : 150,
                appendUnicode      : false,
                normalize          : true,
                centerHorizontally : true,
                formats            : ['ttf', 'eot', 'woff', 'woff2'],
                autohint           : true,
                timestamp          : Math.round(Date.now() / 1000),
            }))
            .on('glyphs', function (glyphs, options) {
                console.log(glyphs, options);
                gulp
                    .src(config.sourceDir + 'core/icon-font/icon-template.scss')
                    .pipe($.consolidate('lodash', {
                        glyphs: glyphs,
                        fontName: fontName,
                        fontPath: '../fonts/',
                        className: 'icon'
                    }))
                    .pipe($.rename(fontName + '.scss'))
                    .pipe(gulp.dest(config.sourceDir + 'core/icon-font/'));
                gulp
                    .src(config.sourceDir + 'core/icon-font/' + fontName + '.scss')
                    .pipe($.plumber()) // exit gracefully if something fails after this
                    .pipe($.sass({
                        outputStyle: 'expanded'
                    }))
                    .pipe($.rename(fontName + '-gallery.css'))
                    .pipe(gulp.dest(config.sourceDir + 'core/icon-font/'));
                gulp
                    .src(config.sourceDir + 'core/icon-font/icon-gallery-template.html')
                    .pipe($.consolidate('lodash', {
                        glyphs: glyphs,
                        fontName: fontName,
                        fontPath: '../fonts/',
                        targetPath: '../../fonts/',
                        className: 'icon'
                    }))
                    .pipe($.rename(fontName + '.html'))
                    .pipe(gulp.dest(config.sourceDir + 'core/icon-font/'));
                cb();
            })
            .pipe(gulp.dest(config.sourceDir + 'fonts/'));
    });

    gulp.task('clean-icon-font-cache', function () {
        delete $.cached.caches[cacheName];
        $.remember.forgetAll(cacheName);
    });

    gulp.task('icon-watcher', function () {
        watch(iconSrc, ['icon-font']);
    });
};
