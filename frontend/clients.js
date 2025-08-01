document.addEventListener("DOMContentLoaded", async function() {
    const serverId = new URLSearchParams(window.location.search).get('server_id');
    const serverDetails = document.getElementById("server-details");
    const clientsTableBody = document.querySelector("#clients-table tbody");
    const modal = document.getElementById("client-modal");
    const closeButton = document.querySelector(".close-button");

    if (!serverId) {
        window.location.href = "/management";
        return;
    }

    serverDetails.textContent = `Server ID: ${serverId}`;

    async function loadClients() {
        try {
            const response = await fetch(`/api/servers/${serverId}/clients`);
            const clients = await response.json();

            clientsTableBody.innerHTML = ""; // Clear existing rows

            if (response.ok) {
                clients.forEach(client => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${client.email}</td>
                        <td>
                            <button onclick="showClient(${client.id})">Show</button>
                            <button onclick="deleteClient(${serverId}, ${client.id})">Delete</button>
                        </td>
                    `;
                    clientsTableBody.appendChild(row);
                });
            } else {
                clientsTableBody.innerHTML = `<tr><td colspan="2">Error loading clients: ${clients.detail}</td></tr>`;
            }
        } catch (error) {
            clientsTableBody.innerHTML = `<tr><td colspan="2">An unexpected error occurred: ${error.message}</td></tr>`;
        }
    }

    await loadClients();

    document.getElementById("add-client-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`/api/servers/${serverId}/clients`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                await loadClients();
                event.target.reset();
            } else {
                const result = await response.json();
                alert(`Error adding client: ${result.detail}`);
            }
        } catch (error) {
            alert(`An unexpected error occurred: ${error.message}`);
        }
    });

    closeButton.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});

async function showClient(clientId) {
    try {
        const response = await fetch(`/api/clients/${clientId}`);
        const data = await response.json();

        if (response.ok) {
            document.getElementById("modal-uuid").textContent = data.uuid;
            document.getElementById("modal-link").textContent = data.vless_link;
            document.getElementById("modal-qr").src = `data:image/png;base64,${data.qr_code}`;
            document.getElementById("client-modal").style.display = "block";
        } else {
            alert(`Error showing client: ${data.detail}`);
        }
    } catch (error) {
        alert(`An unexpected error occurred: ${error.message}`);
    }
}

async function deleteClient(serverId, clientId) {
    if (confirm("Are you sure you want to delete this client?")) {
        try {
            const response = await fetch(`/api/servers/${serverId}/clients/${clientId}`, {
                method: "DELETE"
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const result = await response.json();
                alert(`Error deleting client: ${result.detail}`);
            }
        } catch (error) {
            alert(`An unexpected error occurred: ${error.message}`);
        }
    }
}
