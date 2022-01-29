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
const SPEED = 120;
const SIMPLIFY = false;
const VERBOSE = false;

let beginTime = Date.now();
let previousElapsedSeconds = 0;

let lines = [];
let polylines = [];

function simplify(latlngs)
{
    if (SIMPLIFY)
    {
        return L.LineUtil.simplify(latlngs);
    }
    return latlngs;
}

setInterval(() => {
   const elapsedSeconds = Math.round(((Date.now() - beginTime) / 1000) * SPEED);
   if (VERBOSE) {
       console.log("Elapsed Time: ", elapsedSeconds, "(", elapsedSeconds - previousElapsedSeconds, ")");
   }

    const linesLen = lines.length;
    for (let i = 0; i < linesLen; i++) {
        const line = lines[i];

        if (line['lastPoint'] + 1 === line['end']) {
            continue;
        }

        const points = line['points'];

        if (polylines.length <= i) {
            const polyline = L.polyline([], {
                color: 'red', 
                interactive: false,
                lineJoin: 'miter',
                stroke: true,
                weight: 1,
                opacity: 0.75,
            });
            polyline.addTo(map)
            polylines.push(polyline);
        }

        const polyline = polylines[i];
        
        setTimeout(() => {
            let redraw = false;
            let j = line['lastPoint'];
            for (; j < line['end']; j++) {
                line['lastPoint'] = j;
                if (line['pointTimes'][j] > elapsedSeconds) {
                    break;
                }
                redraw = true;
                data = points.slice(0, j);
            }
            if (redraw) { 
                polyline.setLatLngs(simplify(points.slice(0, j)));
            }
        }, 0);
    }
    previousElapsedSeconds = elapsedSeconds;

}, 1000/FRAMES_PER_SECOND);

let bounds = L.latLngBounds();

function onFilesSelected(e) {
    const numSelectedFiles = e.target.files.length;
    let openFiles = 0;

    const polylinesLen = polylines.length;
    for (let i = 0; i < polylinesLen; i++) {
        polylines[i].removeFrom(map);
    }

    let newLines = [];

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
            end: trkpts.length - 1,
        };

        const len = trkpts.length; 
        for (let i = 0; i < len; i++) {
            const trkpt = trkpts[i];

            const pointTime = (new Date(trkpt.getElementsByTagName('time')[0].textContent) - startTime) / 1000;

            const lat = trkpt.getAttribute('lat');
            const lon = trkpt.getAttribute('lon');
            const point = L.latLng(lat, lon);

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
            map.fitBounds(bounds);
            beginTime = Date.now(); 
            previousElapsedSeconds = 0;
            polylines = [];
            lines = newLines;
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
