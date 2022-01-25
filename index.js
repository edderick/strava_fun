var map = L.map('map').setView([51.505, -0.09], 13);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZXNlYWJyb29rIiwiYSI6ImNreXRlM2ljNzFjdG8yd20xZG9zeGJidmQifQ.pqA117z2Fm5zPbzdY1_WhA', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'your.mapbox.access.token'
}).addTo(map);

const FRAMES_PER_SECOND = 15;
const SPEED = 120;

const beginTime = Date.now();
let previousElapsedSeconds = 100000000;

let lines = [];
let polylines = [];

setInterval(() => {
   const elapsedSeconds = Math.round(((Date.now() - beginTime) / 1000) * SPEED);
   // console.log("Elapsed Time: ", elapsedSeconds);

    const len = lines.length;
    for (let i = 0; i < len; i++)
    {
        // console.log("Rendering the line");
        const line = lines[i];
        const points = line['points'];

        if (polylines.length <= i)
        {
            // console.log("Adding the line");
            let latlngs = [];
            // Draw all the frames from the past
            // TODO: while loop
            for (let j = 0; j < line['end']; j++)
            {
                if (points[j]['pointTime'] > previousElapsedSeconds)
                {
                    line['lastPoint'] = j - 1;
                    break;
                }
                latlngs.push(points[j]['point']);
            }

            const polyline = L.polyline(latlngs, {
                color: 'green', 
                interactive: false,
                lineJoin: false,
            });
            polyline.addTo(map)
            polylines.push(polyline);
        }

        const polyline = polylines[i];
    
        for (let j = line['lastPoint']; j < line['end']; j++)
        {
            if (points[j]['pointTime'] > elapsedSeconds)
            {
                line['lastPoint'] = j - 1;
                break;
            }
            polyline.addLatLng(points[j]['point']);
        }
    }
    previousElapsedSeconds = elapsedSeconds;

}, 1000/FRAMES_PER_SECOND);

let bounds = L.latLngBounds();

function onFilesSelected(e) {

    const onLoad = e => {
        console.log("onLoad ", e);

        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(e.target.result, "text/xml");
        const trkpts = xmlDoc.getElementsByTagName('trkpt');
        
        const startTime = new Date(trkpts[0].getElementsByTagName('time')[0].textContent);
        const beginTime = Date.now();

        let line = {
            points: [],
            lastPoint: 0,
            end: trkpts.length,
        };

        const len = trkpts.length; 
        for (let i = 0; i < len; i++) {
            const trkpt = trkpts[i];

            const pointTime = (new Date(trkpt.getElementsByTagName('time')[0].textContent) - startTime) / 1000;

            const lat = trkpt.getAttribute('lat');
            const lon = trkpt.getAttribute('lon');
            const point = L.latLng(lat, lon);

            bounds.extend(point);

            line['points'].push({
                pointTime,
                point
            });
    
            // TODO: 
            // Figure out how to draw multiple spans. See Manhattan Perimiter for a test case 
        }
        lines.push(line);

        map.fitBounds(bounds);
    }

    const len = e.target.files.length;
    for (let i = 0; i < len; i++) {
        console.log("reading ", e.target.files[i]);

        var fr = new FileReader();
        fr.onload = onLoad;
        fr.readAsText(e.target.files[i]);
    }
}

