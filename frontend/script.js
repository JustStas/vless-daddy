console.log("VLESS Proxy Manager script loaded");

document.getElementById("create-proxy-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "Creating proxy...";

    try {
        const response = await fetch("/api/proxy", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `
                <h3>Proxy Created Successfully!</h3>
                <p>Connection Link:</p>
                <pre><code>${result.vless_link}</code></pre>
                <p>QR Code:</p>
                <img src="data:image/png;base64,${result.qr_code}" alt="QR Code">
            `;
        } else {
            resultDiv.innerHTML = `<p>Error: ${result.detail}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p>An unexpected error occurred: ${error.message}</p>`;
    }
});
