console.log("VLESS Proxy Manager script loaded");

document.getElementById("create-proxy-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    const statusContainer = document.getElementById("status-container");
    const finalResultDiv = document.getElementById("final-result");
    const resultDiv = document.getElementById("result");

    resultDiv.innerHTML = "";
    finalResultDiv.innerHTML = "";
    statusContainer.style.display = "block";

        // Reset status icons
    document.querySelectorAll('#status-steps li span').forEach(span => {
        span.textContent = '○';
    });

    const response = await fetch("/api/proxy", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim() !== '');

        for (const line of lines) {
            if (line.startsWith("status:")) {
                const parts = line.substring("status:".length).split(':');
                const step = parts[0];
                const state = parts[1];
                const stepElement = document.getElementById(`step-${step}`);
                if (stepElement) {
                    if (state === 'inprogress') {
                        stepElement.querySelector('span').textContent = '⌛';
                    } else if (state === 'done') {
                        stepElement.querySelector('span').textContent = '✅';
                    }
                }
            } else if (line.startsWith("result:")) {
                const result = JSON.parse(line.substring("result:".length));
                finalResultDiv.innerHTML = `
                    <h3>Proxy Created Successfully!</h3>
                    <p>Connection Link:</p>
                    <pre><code>${result.vless_link}</code></pre>
                    <p>QR Code:</p>
                    <img src="data:image/png;base64,${result.qr_code}" alt="QR Code">
                `;
            } else if (line.startsWith("error:")) {
                const error = line.substring("error:".length);
                resultDiv.innerHTML = `<p>Error: ${error}</p>`;
                statusContainer.style.display = "none";
            }
        }
    }
});
