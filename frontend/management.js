document.addEventListener("DOMContentLoaded", async function() {
    const serversTableBody = document.querySelector("#servers-table tbody");

    try {
        const response = await fetch("/api/servers");
        const servers = await response.json();

        if (response.ok) {
            servers.forEach(server => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${server.proxy_name}</td>
                    <td>${server.server_ip}</td>
                    <td>${server.mask_domain}</td>
                    <td><button onclick="manageClients(${server.id})">Manage Clients</button></td>
                `;
                serversTableBody.appendChild(row);
            });
        } else {
            serversTableBody.innerHTML = `<tr><td colspan="4">Error loading servers: ${servers.detail}</td></tr>`;
        }
    } catch (error) {
        serversTableBody.innerHTML = `<tr><td colspan="4">An unexpected error occurred: ${error.message}</td></tr>`;
    }
});

function manageClients(serverId) {
    window.location.href = `/clients?server_id=${serverId}`;
}
