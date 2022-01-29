var map = L.map('map').setView([51.505, -0.09], 13);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'eseabrook/ckyz7w9xw000q15kbv0db8ti9',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoiZXNlYWJyb29rIiwiYSI6ImNreXRlM2ljNzFjdG8yd20xZG9zeGJidmQifQ.pqA117z2Fm5zPbzdY1_WhA'
}).addTo(map);

const FRAMES_PER_SECOND = 12;
const SIMPLIFY = false;
const VERBOSE = false;

let speed = parseInt(document.getElementById('speed').value, 10);
let lines = [];

/**
 * Helper fuction to allow disabling siplifying the lines
 */
function simplify(latlngs) {
    if (SIMPLIFY) {
        return L.LineUtil.simplify(latlngs);
    }
    return latlngs;
}

let elapsedSeconds = 0;
let totalSeconds = 0;

setInterval(() => {
    time.textContent = secondsToTimestamp(elapsedSeconds);

    const linesLen = lines.length;
    for (let i = 0; i < linesLen; i++) {
        const line = lines[i];

        // TODO: Find more times we can skip rendering
        if (elapsedSeconds >= line['lastTime'] && line['lastTime'] === line['endTime']) {
            continue;
        }
        
        // TODO: Binary search for the time
        let j = 0;
        for (; j <= line['end']; j++) {
            if (line['pointTimes'][j] > elapsedSeconds) {
                break;
            }
            line['lastPoint'] = j;
            line['lastTime'] = line['pointTimes'][j];
        }
        if (j != line['lastPoint']) { 
            setTimeout(() => {
                line['polylines'][line['polylines'].length - 1].setLatLngs(simplify(line['points'].slice(0, j)));
            }, 0);
        }
    }

}, 1000 / FRAMES_PER_SECOND);

// TODO: Add a loading spinner?
function onFilesSelected(e) {
    pause();

    const bounds = L.latLngBounds();
    const numSelectedFiles = e.target.files.length;

    let openFiles = 0;
    totalSeconds = 0;

    const linesLen = lines.length;
    for (let j = 0; j < linesLen; j++) {
        const polylinesLen = lines[j]['polylines'].length;
        for (let i = 0; i < polylinesLen; i++) {
            if (VERBOSE) {
                console.log('clearing', j, i);
            }
            lines[j]['polylines'][i].removeFrom(map);
        }
    }

    let newLines = [];

    polylines = [];

    const onLoad = e => {
        if (VERBOSE) {
            console.log("onLoad ", e);
        }

        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(e.target.result, "text/xml");
        const trkpts = xmlDoc.getElementsByTagName('trkpt');
        
        const startTime = new Date(trkpts[0].getElementsByTagName('time')[0].textContent);

        let line = {
            points: [],
            pointTimes: [],
            lastPoint: 0,
            lastTime: 0,
            end: trkpts.length - 1,
            endTime: 0,
            polylines: [],
        };

        const polyline = L.polyline([], {
            color: 'red', 
            interactive: false,
            lineJoin: 'miter',
            stroke: true,
            weight: 1,
            opacity: 0.75,
        });
        polyline.addTo(map)
        line['polylines'].push(polyline);

        const len = trkpts.length; 
        for (let i = 0; i < len; i++) {
            const trkpt = trkpts[i];

            const pointTime = (new Date(trkpt.getElementsByTagName('time')[0].textContent) - startTime) / 1000;

            const lat = trkpt.getAttribute('lat');
            const lon = trkpt.getAttribute('lon');
            const point = L.latLng(lat, lon);

            // TODO: Do this better
            line['endTime'] = pointTime;
            if (pointTime > totalSeconds)
            {
                totalSeconds = pointTime;
            }

            bounds.extend(point);

            line['pointTimes'].push(pointTime);
            line['points'].push(point);

            // TODO: 
            // Figure out how to draw multiple spans. See Manhattan Perimiter for a test case 
        }

        newLines.push(line);

        if (VERBOSE) {
            console.log(openFiles, numSelectedFiles);
        }

        openFiles++;

        if (openFiles == numSelectedFiles) {
            reset();
            map.fitBounds(bounds);
            lines = newLines;
            play();
        }
    }

    for (let i = 0; i < numSelectedFiles; i++) {
        if (VERBOSE) {
            console.log("reading ", e.target.files[i]);
        }

        var fr = new FileReader();
        fr.onload = onLoad;
        fr.readAsText(e.target.files[i]);
    }
}

let stepperKey;

function onTimeSelected(e) {
    elapsedSeconds = e.target.value * totalSeconds;
}

function secondsToTimestamp(totalSeconds) {
    const hours = `${Math.floor(totalSeconds / (60 * 60))}`;
    const minutes = `${Math.floor((totalSeconds / 60) % 60)}`.padStart(2, 0);
    const seconds = `${Math.floor((totalSeconds % 60))}`.padStart(2, '0');

    return `${hours}h ${minutes}m ${seconds}s`;
}

function play() {
    clearInterval(stepperKey);

    const slider = document.getElementById('slider');
    const time = document.getElementById('time');

    stepperKey = setInterval(() => {
        if (elapsedSeconds >= totalSeconds) {
            return;
        }
        elapsedSeconds += Math.min((speed / FRAMES_PER_SECOND), totalSeconds);
        slider.value = elapsedSeconds / totalSeconds;

    }, (1000 / FRAMES_PER_SECOND));
}

function pause() {
    clearInterval(stepperKey);
}

function reset() {
    document.getElementById("slider").value = '0';
    elapsedSeconds = 0;
}

function onPlayClicked(e) {
    play();
}

function onPauseClicked(e) {
    pause();
}

function onResetClicked(e) {
    reset();
}

function onSpeedSelected(e)
{
    speed = parseInt(e.target.value, 10);
}
