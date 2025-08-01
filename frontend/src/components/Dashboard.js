import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function Dashboard() {
    const [servers, setServers] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch('/api/servers')
            .then(res => res.json())
            .then(data => setServers(data))
            .catch(err => setError('Could not fetch servers. Is the backend running?'));
    }, []);

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
