import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function Clients() {
    const { serverId } = useParams();
    const [clients, setClients] = useState([]);
    const [traffic, setTraffic] = useState({});
    const [error, setError] = useState(null);
    const [selectedClient, setSelectedClient] = useState(null);

    const fetchClients = useCallback(() => {
        fetch(`/api/servers/${serverId}/clients`)
            .then(res => res.json())
            .then(data => setClients(data))
            .catch(() => setError('Could not fetch clients.'));
    }, [serverId]);

    const fetchTraffic = useCallback(() => {
        setTraffic({}); // Clear old data while fetching
        fetch(`/api/servers/${serverId}/traffic`)
            .then(res => res.json())
            .then(data => setTraffic(data))
            .catch(() => console.error('Could not fetch traffic data.'));
    }, [serverId]);

    useEffect(() => {
        fetchClients();
        fetchTraffic();
    }, [fetchClients, fetchTraffic]);

    const handleAddClient = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = { client_username: formData.get('client_username') };

        await fetch(`/api/servers/${serverId}/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        fetchClients();
        event.target.reset();
    };

    const handleDeleteClient = async (clientId) => {
        if (window.confirm("Are you sure you want to delete this client?")) {
            await fetch(`/api/servers/${serverId}/clients/${clientId}`, { method: 'DELETE' });
            fetchClients();
        }
    };

    const handleShowClient = async (clientId) => {
        const res = await fetch(`/api/clients/${clientId}`);
        const data = await res.json();
        setSelectedClient(data);
    };

    const handleResetTraffic = async () => {
        if (window.confirm("Are you sure you want to reset all traffic data for this server? This action cannot be undone.")) {
            await fetch(`/api/servers/${serverId}/reset_traffic`, { method: 'POST' });
            fetchTraffic();
        }
    };

    return (
        <div>
            <header>
                <h1>Client Management</h1>
                <Link to="/" className="btn-secondary">Back to Dashboard</Link>
            </header>

            {error && <p className="error">{error}</p>}

            <div className="content-split">
                <div className="main-content">
                    <header>
                        <h2>Clients for Server {serverId}</h2>
                        <div>
                            <button className="btn-secondary" onClick={fetchTraffic}>Refresh Traffic</button>
                            <button className="btn-danger" onClick={handleResetTraffic}>Reset Traffic</button>
                        </div>
                    </header>
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Traffic Usage (Up/Down)</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {clients.map(client => {
                                const clientTraffic = traffic[client.username] || { up: 0, down: 0 };
                                const totalTraffic = clientTraffic.up + clientTraffic.down;
                                return (
                                    <tr key={client.id}>
                                        <td>{client.username}</td>
                                        <td>{formatBytes(totalTraffic)} ({formatBytes(clientTraffic.up)} / {formatBytes(clientTraffic.down)})</td>
                                        <td>
                                            <button className="btn-small" onClick={() => handleShowClient(client.id)}>Show</button>
                                            <button className="btn-small btn-danger" onClick={() => handleDeleteClient(client.id)}>Delete</button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                <aside className="sidebar">
                    <h3>Add New Client</h3>
                    <form onSubmit={handleAddClient}>
                        <label>Client Username:</label>
                        <input type="text" name="client_username" required />
                        <button type="submit">Add Client</button>
                    </form>
                </aside>
            </div>

            {selectedClient && (
                <div className="modal-backdrop" onClick={() => setSelectedClient(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h2>Client Details</h2>
                        <p><strong>UUID:</strong> {selectedClient.uuid}</p>
                        <p><strong>Connection Link:</strong></p>
                        <div className="link-container">
                            <pre><code>{selectedClient.vless_link}</code></pre>
                            <button onClick={() => navigator.clipboard.writeText(selectedClient.vless_link)}>📋</button>
                        </div>
                        <p><strong>QR Code:</strong></p>
                        <img src={`data:image/png;base64,${selectedClient.qr_code}`} alt="QR Code" />
                        <button className="btn-secondary" onClick={() => setSelectedClient(null)}>Close</button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Clients;
