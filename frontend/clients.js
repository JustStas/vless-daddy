document.addEventListener("DOMContentLoaded", async function() {
    const serverId = new URLSearchParams(window.location.search).get('server_id');
    const serverDetails = document.getElementById("server-details");
    const clientsTableBody = document.querySelector("#clients-table tbody");

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
                        <td>${client.uuid}</td>
                        <td><button onclick="deleteClient(${serverId}, ${client.id})">Delete</button></td>
                    `;
                    clientsTableBody.appendChild(row);
                });
            } else {
                clientsTableBody.innerHTML = `<tr><td colspan="3">Error loading clients: ${clients.detail}</td></tr>`;
            }
        } catch (error) {
            clientsTableBody.innerHTML = `<tr><td colspan="3">An unexpected error occurred: ${error.message}</td></tr>`;
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
});

async function deleteClient(serverId, clientId) {
    if (confirm("Are you sure you want to delete this client?")) {
        try {
            const response = await fetch(`/api/servers/${serverId}/clients/${clientId}`, {
                method: "DELETE"
            });

            if (response.ok) {
                // The loadClients function is not in this scope, so we reload the page
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
