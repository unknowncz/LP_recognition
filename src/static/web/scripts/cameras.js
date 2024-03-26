
main = document.getElementById('main');

function setupjsinterrupt(id) {
    deleteelem = main.getElementsByTagName('div')[main.childElementCount-2];
    buttonelem = main.lastChild;
    // [live feed] [crop (disabled)]     [separator]     [reset] [apply]
    buttonelem.children[0].addEventListener('click', function() {
        // TODO: grab arguments from the form and open a new window with the live feed
        //window.open('/cameras/live', '_blank');
    });
    buttonelem.children[3].addEventListener('click', function() {
        setcamera(id);
    });
    buttonelem.children[4].addEventListener('click', function() {
        // send a request to the server to apply the crop
        // TODO: grab arguments from the form and send them to the server
    });
}

function resetcamera() {
    window.location.reload();
}

function setcamera(id) {
    console.log('Setting camera to ' + id);
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/cameras?config='+id, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Camera set to ' + id);
            html = xhr.responseText;
            main.innerHTML = html;
            setupjsinterrupt(id);
        }
    }
    xhr.send();
}


sidebar = document.getElementById('sidenav');
cameras = sidebar.getElementsByTagName('a');

function addcameraselector() {
    newElement = document.createElement('a');
    newElement.innerHTML = 'Camera ' + (cameras.length-2);
    newElement.id = cameras.length-2;
    newElement.removeEventListener
    newElement.addEventListener('click', function(e) {
        setcamera(this.id);
    });
    sidebar.insertBefore(newElement, cameras[cameras.length-2]);
}

function addcamera() {
    console.log(this)
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/cameras?add=1', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Added camera');
            // add the new camera to the sidebar
            setcamera(cameras.length-2);
            addcameraselector();
        }
    }
    xhr.send();
}


for (let i = 0; i < cameras.length-2; i++) {
    cameras[i].addEventListener('click', function() {
        setcamera(this.id);
    });
}
cameras[cameras.length-2].addEventListener('click', addcamera);