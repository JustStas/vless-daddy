# VLESS Daddy

VLESS Daddy is a simple, locally-run web application designed to help users easily create and manage VLESS proxies with XTLS-Reality on remote servers. It provides a modern, user-friendly interface to automate the entire setup and client management process, removing the need for manual SSH commands and configuration.

## Features

-   **Guided Proxy Setup:** A step-by-step process with real-time status updates for setting up a new proxy server.
-   **Modern UI:** A clean and responsive user interface built with React.
-   **Management Dashboard:** A central dashboard to view all your managed proxy servers.
-   **Client Management:** Easily add or remove clients (users) for each of your servers.
-   **Connection Details:** Automatically generates VLESS links and QR codes for easy client configuration.
-   **Safety First:** Includes a confirmation step to prevent accidental overwriting of existing server configurations.

## Technology Stack

-   **Backend:** Python with the **FastAPI** framework and **Paramiko** for SSH connections.
-   **Frontend:** **React** (bootstrapped with Create React App) and **React Router** for navigation.
-   **Database:** **SQLite** for simple, local storage of server and client information.

## Getting Started

### Prerequisites

-   Python 3.8+
-   Node.js and npm

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd vless-daddy
    ```

2.  **Set up the Backend:**
    Install the required Python packages.
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Set up the Frontend:**
    Navigate to the frontend directory, install dependencies, and build the production version of the app.
    ```bash
    cd frontend
    npm install
    npm run build
    ```

## How to Run

1.  **Start the Backend Server:**
    From the project's root directory, run the following command:
    ```bash
    python backend/main.py
    ```
    The server will start, and the application will be ready.

2.  **Access the Web Interface:**
    Open your web browser and navigate to `http://localhost:8000`. You will be greeted with the management dashboard.

## Development

-   **Backend:** The FastAPI server is configured to auto-reload when you make changes to the backend Python files.
-   **Frontend:** For a better development experience with hot-reloading for the UI, you can run the React development server. In a new terminal, navigate to the `frontend` directory and run:
    ```bash
    cd frontend
    npm start
    ```
    This will typically open the app at `http://localhost:3000` and will proxy API requests to your backend running on port 8000.

## Important Notes

-   The database file, `vless_daddy.db`, is created automatically in the root directory and is excluded from Git via the `.gitignore` file.
-   If you pull new changes that include a database schema update, you may need to delete your local `vless_daddy.db` file for the application to create a new one with the correct structure. **This will delete all saved server data.**
