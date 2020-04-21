const { series, parallel, src, dest } = require('gulp');
const uglify = require('gulp-uglify');
const rename = require('gulp-rename');
const gulpif = require('gulp-if');
const del = require('del');
const concat = require('gulp-concat');
const strip = require('gulp-strip-comments')
const exec = require('child_process').exec;
const cleanCSS = require('gulp-clean-css');
const processhtml = require('gulp-processhtml');
const fs = require('fs');
const bump = require('gulp-bump');
const PluginError = require('plugin-error');
const git = require('gulp-git');
const dateTime = require('date-time');

const PROJECT = '{{cookiecutter.app_name}}'

/* Test task to run a command */
function childProcessTask(cb) {
  exec(`python ./${PROJECT}/manage.py`, function(err, stdout, stderr) {
    console.log(stdout);
    console.log(stderr);
    cb(err);
  });
}

function getPackageJsonVersion () {
  // We parse the json file instead of using require because require caches
  // multiple calls so the version number won't be updated
  return JSON.parse(fs.readFileSync('./package.json', 'utf8')).version;
};

/* Cleans up the dist folder */
function clean() {
  return del('dist/');
}

/*
 * Returns a boolean indicating if the supplied javascript file is not minified.
 * Uses the filenaming convention of using .min.js to determine this.
 */
function isUnminifiedJavascript(file) {
  return file.extname === '.js' && !file.basename.endsWith('.min.js');
}

/*
 * Returns TRUE if the stream being processed belongs to file
 * 'public/templates/templates/public/home_page.html'
 */
function isHTML(file) {
  return file.extname === '.html';
}

function isCSS(file) {
  return file.extname === '.css';
}

function doBuild(cb) {
  let pkg = JSON.parse(fs.readFileSync('./package.json'));
  console.log('Version: ' + pkg.version);
  return src([
      'src/**/*',
      '!src/**/__pycache__',
      '!src/**/*.pyc',
      '!src/**/*.log',
      '!src/*.sqlite3',
    ], { base: 'src' })
    .pipe(gulpif(isHTML, processhtml({
      data: {
        siteVersion: pkg.version,
        buildTime: dateTime()
      }
    })))
    .pipe(gulpif(isCSS, cleanCSS({rebase: false})))
    .pipe(gulpif(isUnminifiedJavascript, uglify()))
    .pipe(gulpif(isUnminifiedJavascript, rename({ extname: '.min.js' })))
    .pipe(dest('dist'));
}

/* Task to bump version number */
function bumpVersion(cb) {
  return src('./package.json')
    .pipe(bump({type: buildOptions.release}))
    .pipe(dest('./'));
}

function commitChanges() {
  return gulp.src('.')
    .pipe(git.add())
    .pipe(git.commit('[Prerelease] Bumped version number'));
}

function pushChange (done) {
  git.push('origin', 'master', done);
}

function createNewTag(done) {
  var version = getPackageJsonVersion();
  git.tag(version, 'Created Tag for version: ' + version, function (error) {
    if (error) {
      return done(error);
    }
    git.push('origin', 'master', {args: '--tags'}, done);
  });

}

/**
 * Write version.txt with the current version read from package.json
 * to dist/version.txt
 */
function emitVersion(cb) {
  var version = getPackageJsonVersion();
  fs.writeFile('dist/version.txt', version, cb);
}


/*
  PROCESS SCRIPT COMMAND LINE ARGUMENTS
 */

// Default build options
let DEFAULT_BUILD_OPTIONS = {
  type: 'stage',    // {stage|release}
  release: 'patch', // {major|minor|patch}
  tests: 'no'       // {yes|no}
};

// fetch command line arguments
let userBuildOptions = (argList => {

  let arg = {}, a, opt, thisOpt, curOpt;
  for (a = 0; a < argList.length; a++) {

    thisOpt = argList[a].trim();
    opt = thisOpt.replace(/^\-+/, '');

    if (opt === thisOpt) {
      // argument value
      if (curOpt) arg[curOpt] = opt;
      curOpt = null;
    } else {
      // argument name
      curOpt = opt;
      arg[curOpt] = true;
    }
  }
  return arg;
})(process.argv);

const buildOptions = Object.assign({}, DEFAULT_BUILD_OPTIONS, userBuildOptions);

// Verify build option values

// build type
if (['stage', 'release'].indexOf(buildOptions.type) < 0) {
  throw new PluginError('params', 'Invalid value specified for "type" parameter. Valid values are {stage|release}');
}

// release type
if (['major', 'minor', 'patch'].indexOf(buildOptions.release) < 0) {
  throw new PluginError('params', 'Invalid value specified for "release" parameter. Valid values are {major|minor|patch}');
}

// tests
if (['yes', 'no'].indexOf(buildOptions.tests) < 0) {
  throw new PluginError('params', 'Invalid value specified for "tests" parameter. Valid values are {yes|no}.');
}

exports.clean = clean;

exports.build = series(clean, doBuild)

// exports.buildHomePageJS = buildHomePageJS;
// exports.buildHomePageCSS = buildHomePageCSS;
exports['bump-version'] = bumpVersion;

exports.release = series(
  clean,
  doBuild,
  emitVersion,
  bumpVersion
)

exports.default = series(
  clean,
  doBuild,
  emitVersion,
  );
