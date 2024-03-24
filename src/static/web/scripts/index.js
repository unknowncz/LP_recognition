logs = document.getElementById('logContainer')
const ws = new WebSocket('ws://'+document.location.hostname+':5001/test')

// Connection opened
ws.addEventListener("open", (event) => {
  ws.send("Hello Server!");
});

// Listen for messages
ws.addEventListener("message", (event) => {
  console.log("Message from server ", event.data);
});