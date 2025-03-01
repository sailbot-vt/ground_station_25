self.addEventListener('fetch', function (event) {
    if (event.request.url.endsWith('/send-data')) {
        event.respondWith(handleRequest(event.request));
    }
});

async function handleRequest(request) {
    const requestData = await request.json(); // assuming JSON payload

    // Process the data (e.g., store, log, etc.)
    console.log('Received data:', requestData);

    // Send a response
    const responseData = {
        status: 'success',
        received_data: requestData
    };

    return new Response(JSON.stringify(responseData), {
        headers: { 'Content-Type': 'application/json' }
    });
}
