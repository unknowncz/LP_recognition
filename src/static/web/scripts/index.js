logs = document.getElementById('logContainer')

const ws = io("ws://127.0.0.1:5000/");

function addLog(logtime, loglevel, logmsg) {
    newlog = document.createElement('div')
    newlog.innerHTML = `<span class="logtime">${logtime}</span> <span class="loglevel">${loglevel}</span> <span class="logmsg">${logmsg}</span>`
    logs.appendChild(newlog)
}

function addMalformedLog(log) {
    newlog = document.createElement('div')
    newlog.innerHTML = `<span class="logmalformed">${log}</span>`
    logs.appendChild(newlog)
}

ws.on('connect', () => {
    console.log('Connected to server')
    ws.emit('join', 'client')
})
ws.on('disconnect', () => {
    console.log('Disconnected from server')
})
ws.on('json', (json) => {
    console.log(json)
    if (json['malformed']) {
        addMalformedLog(json['malformed'])
        return
    }
    addLog(json['time'], json['level'], json['message'])
})
