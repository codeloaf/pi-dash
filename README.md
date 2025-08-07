# Pi-Dash: A Minimalist Pi-hole Dashboard

Pi-Dash is a simple, lightweight dashboard for monitoring multiple Pi-hole instances. It provides a clean, at-a-glance, responsive view of your Pi-hole statistics.

## Features

*   **Multiple Pi-hole Support:** Monitor all your Pi-hole instances from a single dashboard.
*   **Dynamic Configuration:** Easily add, remove, or disable Pi-holes through a simple `config.json` file.
*   **Responsive Design:** The layout works on both desktop and mobile devices, stacking cards vertically on smaller screens.
*   **Real-time Statistics:** The dashboard automatically refreshes every second.
*   **Lightweight and Fast:** Built with Flask and vanilla JavaScript, Pi-Dash is fast and has minimal dependencies.
*   **Dark Mode:** Automatically switches theme based on your system preferences.

![pi-dash-landscape](https://github.com/user-attachments/assets/a0e1fbef-279a-40df-9424-0cad50c31b50)

## Configuration

Before running the application, you need to configure the following two files:

**1. `config.json`**

This file manages your Pi-hole instances. Open it and edit the following for each Pi-hole:
*   `name`: A custom name for your Pi-hole (e.g., "Primary").
*   `address`: The full URL to your Pi-hole (e.g., "http://pi.hole").
*   `password`: Your Pi-hole API token/password.
*   `enabled`: Set to `true` to display the Pi-hole on the dashboard, or `false` to hide it.

**2. `manifest.json`** (Optional)

This file is for the Progressive Web App (PWA) icon. 
*   Open `manifest.json` and replace the placeholder URL in the `src` field with a direct link to an icon file. Many users use the logo from their own Pi-hole admin page (e.g., `http://pi.hole/admin/img/logo.svg`).

## Installation

### Docker
1. **Docker Compose**
   ```yaml
   services:
       pi-dash:
           image: ghcr.io/codeloaf/pi-dash:main
           container_name: pi-dash
           ports:
             - 5001:5001
           volumes:
             - /path/to/pi-dash/config.json:/app/config.json
             - /path/to/pi-dash/manifest.json:/app/manifest.json # If you wish to edit the current manifest
   ```
3. **Docker Run**
   ```bash
   docker run -d \
    --name=pi-dash \
    -p 5001:5001 \
    -v /path/to/pi-dash/config.json:/app/config.json \
    -v /path/to/pi-dash/manifest.json:/app/manifest.json \ # If you wish to edit the current manifest
    ghcr.io/codeloaf/pi-dash:main
   ```

### Native Install
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/codeloaf/pi-dash.git
    cd pi-dash
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Start the app:**
   To start the application, run the following command from the project's root directory:
   ```bash
   python proxy.py
   ```

Then, open your web browser and navigate to `http://localhost:5001`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.
