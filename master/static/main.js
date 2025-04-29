// Mapping step → SSE port
const containerPorts = {
    scraper: 7000,
    chunker: 7001,
    embedder: 7002
};

// Hold open EventSource objects
const eventSources = {};

// Poll container statuses every 3s
async function updateStatus() {
    const res = await fetch('/containers');
    const statuses = await res.json();

    Object.entries(statuses).forEach(([name, { status, running }]) => {
        // Update badge
        document.getElementById(`${name}-status`).textContent = status;

        // If it's running and we haven't yet connected SSE, do it now
        if (running && !(name in eventSources)) {
            connectToSSE(name);
        }
    });
}

// Open an SSE connection for a given container
function connectToSSE(container) {
    const port = containerPorts[container];
    const url = `http://localhost:${port}/events`;

    const source = new EventSource(url);
    eventSources[container] = source;

    source.onmessage = (evt) => {
        try {
            const data = JSON.parse(evt.data);
            // pretty-print JSON into the <pre>
            document.getElementById(`${container}-stats`).textContent =
                JSON.stringify(data, null, 2);
        } catch (err) {
            console.error(`Failed to parse SSE for ${container}:`, err);
        }
    };

    source.onerror = () => {
        // Close on error to avoid infinite reconnection attempts
        document.getElementById(`${container}-stats`).textContent =
            "⚠️ Error receiving stats.";
        source.close();
    };
}

// Wire up your buttons
document.getElementById("start-btn").onclick = () =>
    fetch('/start', { method: "POST" });

document.querySelectorAll(".stop-btn").forEach(btn => {
    btn.onclick = () => {
        const container = btn.getAttribute("data-container");
        fetch(`/stop/${container}`, { method: "POST" });
    };
});

document.getElementById("cron-btn").onclick = async () => {
    const cron = document.getElementById("cron-input").value;
    const res = await fetch('/set-cron', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cron })
    });
    const data = await res.json();
    if (data.error) alert(data.error);
};

// Kick off initial load + polling
updateStatus();
setInterval(updateStatus, 3000);
