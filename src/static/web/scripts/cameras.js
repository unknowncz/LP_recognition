
main = document.getElementById('main');

function setcamera(id) {
    console.log('Setting camera to ' + id);
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/cameras?config='+id, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Camera set to ' + id);
            html = xhr.responseText;
            main.innerHTML = html;
        }
    }
    xhr.send();
}

sidebar = document.getElementById('sidenav');
cameras = sidebar.getElementsByTagName('a');
for (let i = 0; i < cameras.length-2; i++) {
    cameras[i].addEventListener('click', function() {
        setcamera(0);
    });
}
cameras[cameras.length-2].addEventListener('click', function() {
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/cameras?add=1', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Added camera');
            setcamera(cameras.length-2);
        }
    }
    xhr.send();
});