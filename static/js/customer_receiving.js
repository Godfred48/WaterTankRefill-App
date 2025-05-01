<script>
const deliveryId = "{{ delivery.delivery_id }}";
const socket = new WebSocket(`ws://${window.location.host}/ws/delivery-tracking/${deliveryId}/`);

socket.onopen = () => {
    console.log("WebSocket connected as customer");
};

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === "location_update") {
        const lat = parseFloat(data.lat);
        const lng = parseFloat(data.lng);
        console.log("Driver is now at:", lat, lng);

        // If using a map like Leaflet or Google Maps, update the marker
        updateDriverMarker(lat, lng);  // This is your function to move the marker
    }
};

socket.onclose = () => {
    console.warn("WebSocket closed");
};
</script>
