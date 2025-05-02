<script>
const deliveryId = "{{ delivery.delivery_id }}";  // from your Django template
const socket = new WebSocket(`ws://${window.location.host}/ws/delivery-tracking/${deliveryId}/`);

socket.onopen = () => {
    console.log("WebSocket connected as driver");
    // Start sending location every 5 seconds
    setInterval(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                socket.send(JSON.stringify({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                }));
            });
        }
    }, 5000); // every 5 seconds
};

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log("Received message:", data);
};

socket.onclose = () => {
    console.warn("WebSocket closed");
};
</script>
