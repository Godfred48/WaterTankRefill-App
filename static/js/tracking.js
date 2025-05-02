const socket = new WebSocket(`ws://localhost:8000/ws/delivery-tracking/${deliveryId}/`);

socket.onmessage = function(e) {
  const data = JSON.parse(e.data);
  if (data.type === "location_update") {
    // update map marker for driver
    console.log("New driver location:", data.lat, data.lng);
  }
};

function sendDriverLocation(lat, lng) {
  socket.send(JSON.stringify({ lat, lng }));
}
