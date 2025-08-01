import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function Dashboard() {
    const [servers, setServers] = useState([]);
    const [error, setError] = useState(null);

    const fetchServers = () => {
        fetch('/api/servers')
            .then(res => res.json())
            .then(data => setServers(data))
            .catch(err => setError('Could not fetch servers. Is the backend running?'));
    };

    useEffect(() => {
        fetchServers();
    }, []);

        const handleDeleteServer = async (serverId) => {
        const confirmDelete = window.confirm(
            "Are you sure you want to delete this server from the dashboard?\n\nClick 'OK' to delete.\nClick 'Cancel' to keep the server."
        );

        if (confirmDelete) {
            const cleanup = window.confirm(
                "Do you want to also clean up the remote server?\n\nThis will stop the xray service and delete all its files. This action cannot be undone."
            );
            const res = await fetch(`/api/servers/${serverId}?cleanup=${cleanup}`, { method: 'DELETE' });
            if (res.ok) {
                // Remove the server from the local state immediately for a responsive UI
                setServers(prevServers => prevServers.filter(server => server.id !== serverId));
            } else {
                setError("Failed to delete the server. Please try again.");
            }
        }
    };


    return (
        <div>
            <header>
                <h1>Management Dashboard</h1>
                <Link to="/create" className="btn">Create New Server</Link>
            </header>

            {error && <p className="error">{error}</p>}

            <h2>Managed Servers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Proxy Name</th>
                        <th>Server IP</th>
                        <th>Masking Domain</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {servers.length > 0 ? servers.map(server => (
                        <tr key={server.id}>
                            <td>{server.proxy_name}</td>
                            <td>{server.server_ip}</td>
                            <td>{server.mask_domain}</td>
                            <td>
                                <Link to={`/clients/${server.id}`} className="btn-small">Manage Clients</Link>
                                <button onClick={() => handleDeleteServer(server.id)} className="btn-small btn-danger">Delete</button>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan="4">No servers found. Create one to get started!</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default Dashboard;
