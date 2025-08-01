# VLESS Daddy

VLESS Daddy is a simple, locally-run web application designed to help users easily create and manage VLESS proxies with XTLS-Reality on remote servers. It provides a modern, user-friendly interface to automate the entire setup and client management process, removing the need for manual SSH commands and configuration.

## Features

### 🚀 **Proxy Management**
- **Guided Proxy Setup:** Step-by-step process with real-time status updates for setting up new proxy servers
- **Server Overwrite Protection:** Confirmation dialogs prevent accidental overwriting of existing configurations
- **Custom Proxy Naming:** Assign meaningful names to your proxy servers for easy identification
- **Automatic Cleanup:** Old database entries are removed when servers are overwritten

### 👥 **Client Management**
- **Easy Client Addition/Removal:** Add or remove users with a few clicks
- **Automatic Configuration:** Generates VLESS connection links and QR codes automatically
- **Client Details Modal:** View UUIDs, connection strings, and QR codes in a clean interface
- **Copy-to-Clipboard:** One-click copying of connection details

### 📊 **Traffic Monitoring**
- **Real-time Traffic Statistics:** Monitor upload/download traffic for each client
- **Traffic Reset:** Reset traffic counters when needed
- **Bandwidth Usage Display:** Human-readable traffic statistics (KB, MB, GB)
- **Per-user Analytics:** Track individual client usage patterns

### 🎨 **Modern Interface**
- **React-based UI:** Clean, responsive design that works on all devices
- **Real-time Status Updates:** Live progress indicators during proxy creation
- **Management Dashboard:** Central hub for all your proxy servers
- **Intuitive Navigation:** Easy-to-use interface designed for non-technical users

## Technology Stack

- **Backend:** Python with **FastAPI** framework, **Paramiko** for SSH connections, **SQLite** for data storage
- **Frontend:** **React** with **React Router** for navigation and modern component-based architecture
- **Proxy Technology:** **VLESS** protocol with **XTLS-Reality** for enhanced security and performance
- **Server Communication:** **Xray-core** with built-in Statistics API for traffic monitoring
- **Authentication:** SSH key-based server access with automatic Xray installation

## Architecture

```
VLESS Daddy/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main API server and routing
│   ├── proxy_creator.py    # SSH automation for Xray setup
│   ├── client_manager.py   # Client configuration management
│   ├── traffic_parser.py   # Traffic statistics via Xray API
│   ├── database.py         # SQLite database management
│   ├── proxy_verifier.py   # Connection verification
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.js         # Main application and routing
│   │   └── App.css        # Modern styling
│   ├── build/             # Production build (served by backend)
│   └── package.json       # Node.js dependencies
├── README.md              # This file
├── .gitignore            # Git ignore rules
└── vless_daddy.db        # SQLite database (auto-created)
```

## Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** and npm
- **SSH access** to your remote server(s)
- **Root privileges** on the remote server (for Xray installation)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd vless-daddy
   ```

2. **Set up the Backend:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

## How to Run

1. **Start the Application:**
   ```bash
   python backend/main.py
   ```

2. **Access the Web Interface:**
   Open your browser and navigate to `http://localhost:8000`

The application will automatically:
- Initialize the SQLite database
- Serve the React frontend
- Provide API endpoints for proxy management

## Usage Guide

### Creating Your First Proxy

1. Click **"Create New Server"** from the dashboard
2. Fill in the server details:
   - **Server IP:** Your remote server's IP address
   - **SSH User:** Username with root privileges (usually `root`)
   - **SSH Password:** Password for SSH access
   - **Masking Domain:** Domain to mask traffic (e.g., `microsoft.com`)
   - **Proxy Name:** A friendly name for identification
3. Watch the real-time progress as the system:
   - Connects to your server
   - Installs Xray if needed
   - Generates security keys
   - Configures the proxy
   - Verifies the connection

### Managing Clients

1. From the dashboard, click **"Manage Clients"** for any server
2. **Add clients:** Enter a username and click "Add Client"
3. **View connection details:** Click "Show" to see:
   - Client UUID
   - VLESS connection string
   - QR code for mobile apps
4. **Monitor traffic:** View real-time upload/download statistics
5. **Remove clients:** Click "Delete" to remove access

### Traffic Monitoring

- **Real-time Statistics:** Traffic data updates automatically
- **Usage Breakdown:** See both total traffic and upload/download separately
- **Reset Counters:** Use "Reset Traffic" to clear all statistics
- **Refresh Data:** Click "Refresh Traffic" for the latest numbers

## Development

### Backend Development
```bash
python backend/main.py
```
The FastAPI server runs with auto-reload enabled for development.

### Frontend Development
```bash
cd frontend
npm start
```
This starts the React development server with hot-reloading at `http://localhost:3000`, which proxies API requests to the backend.

### API Endpoints

- `GET /api/servers` - List all managed servers
- `POST /api/proxy` - Create a new proxy server
- `GET /api/servers/{id}/clients` - List clients for a server
- `POST /api/servers/{id}/clients` - Add a new client
- `DELETE /api/servers/{id}/clients/{client_id}` - Remove a client
- `GET /api/servers/{id}/traffic` - Get traffic statistics
- `POST /api/servers/{id}/reset_traffic` - Reset traffic counters

## Security Considerations

- **Local Operation:** The application runs locally and stores data in a local SQLite database
- **SSH Security:** Uses standard SSH authentication; consider using SSH keys for enhanced security
- **Traffic Encryption:** All proxy traffic is encrypted using XTLS-Reality
- **No External Dependencies:** No data is sent to external services

## Troubleshooting

### Common Issues

1. **"Connection failed"** - Check SSH credentials and server accessibility
2. **"Xray installation failed"** - Ensure the server has internet access and root privileges
3. **"Traffic shows 0 bytes"** - Generate some traffic through the proxy, then refresh statistics
4. **Database errors** - Delete `vless_daddy.db` to reset (will lose all server data)

### Server Requirements

- **Ubuntu/Debian** Linux distribution (recommended)
- **Root access** for Xray installation
- **Port 443** available for proxy traffic
- **Internet connectivity** for downloading Xray

## Important Notes

- The database file `vless_daddy.db` is automatically created and excluded from Git
- Server data is stored locally - back up the database file if needed
- When updating the application, you may need to delete the database file if the schema changes
- Each proxy server can handle multiple clients with individual traffic tracking
- The application is designed for personal/small-scale use

## Contributing

This project was built to simplify VLESS proxy management for non-technical users. Feel free to contribute improvements, bug fixes, or additional features.

## License

This project is provided as-is for educational and personal use.