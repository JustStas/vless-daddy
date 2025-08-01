import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const stepsConfig = [
    { key: 'cleanup', title: 'Cleaning Server', subtitle: 'Removing old configuration and logs.' },
    { key: 'connect', title: 'Connecting to Server', subtitle: 'Establishing SSH connection...' },
    { key: 'install', title: 'Installing Software', subtitle: 'Ensuring curl and Xray are installed.' },
    { key: 'keys', title: 'Generating Keys', subtitle: 'Creating new UUID and public/private keys.' },
    { key: 'config', title: 'Deploying Configuration', subtitle: 'Uploading config file and restarting service.' },
    { key: 'verify', title: 'Verifying Connection', subtitle: 'Testing the new proxy endpoint.' },
    { key: 'done', title: 'Finalizing', subtitle: 'Saving the new server to the database.' },
];

function Create() {
    const [statuses, setStatuses] = useState({});
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [inProgress, setInProgress] = useState(false);
    const [formData, setFormData] = useState({
        server_ip: '',
        ssh_user: 'root',
        ssh_password: '',
        ssh_port: 22,
        mask_domain: '',
        proxy_name: 'MyProxy'
    });

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const startProxyCreation = async (overwrite = false) => {
        setInProgress(true);
        setStatuses({});
        setResult(null);
        setError(null);

        const payload = { ...formData, overwrite };

        const response = await fetch('/api/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n').filter(line => line.trim() !== '');

                for (const line of lines) {
                    if (line.startsWith("status:")) {
                        const [step, state] = line.substring(7).split(':');
                        setStatuses(prev => ({ ...prev, [step]: state }));
                    } else if (line.startsWith("result:")) {
                        setResult(JSON.parse(line.substring(7)));
                        setInProgress(false);
                    } else if (line.startsWith("error:")) {
                        const errorMsg = line.substring(6);
                        if (errorMsg === 'exists') {
                            if (window.confirm("A proxy configuration already exists on this server. Do you want to overwrite it?")) {
                                await startProxyCreation(true);
                            } else {
                                setError('Operation cancelled by user.');
                                setInProgress(false);
                            }
                        } else {
                            setError(errorMsg);
                            const currentStep = Object.keys(statuses).find(k => statuses[k] === 'inprogress');
                            if (currentStep) {
                                setStatuses(prev => ({ ...prev, [currentStep]: 'error' }));
                            }
                        }
                        return;
                    }
                }
            }
        } finally {
            if (!result) setInProgress(false);
        }
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        startProxyCreation(false);
    };

    return (
        <div>
            <header>
                <h1>Create New Proxy</h1>
                <Link to="/" className="btn-secondary">Back to Dashboard</Link>
            </header>

            <div className="content-split">
                <div className="main-content">
                    <form onSubmit={handleSubmit}>
                        <label>Server IP:</label>
                        <input type="text" name="server_ip" value={formData.server_ip} onChange={handleInputChange} required />

                        <label>SSH User:</label>
                        <input type="text" name="ssh_user" value={formData.ssh_user} onChange={handleInputChange} required />

                        <label>SSH Password:</label>
                        <input type="password" name="ssh_password" value={formData.ssh_password} onChange={handleInputChange} required />

                        <label>SSH Port:</label>
                        <input type="number" name="ssh_port" value={formData.ssh_port} onChange={handleInputChange} required />

                        <label>Masking Domain:</label>
                        <input type="text" name="mask_domain" value={formData.mask_domain} onChange={handleInputChange} required />

                        <label>Proxy Name:</label>
                        <input type="text" name="proxy_name" value={formData.proxy_name} onChange={handleInputChange} required />

                        <button type="submit" disabled={inProgress}>
                            {inProgress ? 'Creating...' : 'Create Proxy'}
                        </button>
                    </form>
                </div>

                <aside className="sidebar">
                    {inProgress && (
                        <div className="timeline">
                            {stepsConfig.map((step, index) => {
                                const status = statuses[step.key] || 'pending';
                                return (
                                    <div key={step.key} className={`timeline-step status-${status}`}>
                                        <div className="timeline-node"></div>
                                        <div className="timeline-content">
                                            <strong>{step.title}</strong>
                                            <p>{step.subtitle}</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </aside>
            </div>

            {error && <p className="error-box"><strong>Error:</strong> {error}</p>}

            {result && (
                <div className="result-box">
                    <h3>Proxy Created Successfully!</h3>
                    <p><strong>Connection Link:</strong></p>
                    <div className="link-container">
                        <pre><code>{result.vless_link}</code></pre>
                        <button onClick={() => navigator.clipboard.writeText(result.vless_link)}>📋</button>
                    </div>
                    <p><strong>QR Code:</strong></p>
                    <img src={`data:image/png;base64,${result.qr_code}`} alt="QR Code" />
                </div>
            )}
        </div>
    );
}

export default Create;
