import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def show_secrets():
    # --- Pattern 1: Check Environment Variables ---
    # The Operator Pattern injects secrets as standard environment variables.
    env_username = os.getenv("SECRET_USERNAME", "Not Set")
    env_message = os.getenv("SECRET_MESSAGE", "Not Set")

    # --- Pattern 2: Check Files ---
    # The Injector Pattern mounts secrets as files in memory.
    file_username = "Not Set"
    file_message = "Not Set"

    try:
        with open("/vault/secrets/username", "r") as f:
            file_username = f.read().strip()
    except FileNotFoundError:
        pass

    try:
        with open("/vault/secrets/message", "r") as f:
            file_message = f.read().strip()
    except FileNotFoundError:
        pass

    # --- Pattern 3: Check Dynamic Database Secret ---
    # This secret is generated on-demand by Vault for this specific pod.
    db_config = "Not Set"
    try:
        with open("/vault/secrets/database-config", "r") as f:
            db_config = f.read().strip()
    except FileNotFoundError:
        pass

    # --- Render HTML ---
    # Renders a simple HTML page to visualize the retrieved secrets.
    html = f"""
    <html>
    <head>
        <title>Secret Reader</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; background-color: #f0f0f0; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; margin-bottom: 20px; }}
            h2 {{ color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            .value {{ font-weight: bold; color: #0066cc; word-break: break-all; }}
            .source {{ font-size: 0.8em; color: #666; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🕵️ Secret Reader App</h1>

            <h2>Pattern 1: Environment Variables</h2>
            <p>Username: <span class="value">{env_username}</span></p>
            <div class="source">Source: os.getenv("SECRET_USERNAME")</div>
            <p>Message: <span class="value">{env_message}</span></p>
            <div class="source">Source: os.getenv("SECRET_MESSAGE")</div>
        </div>

        <div class="card">
            <h2>Pattern 2: Mounted Files</h2>
            <p>Username: <span class="value">{file_username}</span></p>
            <div class="source">Source: /vault/secrets/username</div>
            <p>Message: <span class="value">{file_message}</span></p>
            <div class="source">Source: /vault/secrets/message</div>
        </div>

        <div class="card" style="border-left: 5px solid #00cc66">
            <h2>Pattern 3: Dynamic Secrets 🚀</h2>
            <p>Database Connection String:</p>
            <p class="value">{db_config}</p>
            <div class="source">Source: /vault/secrets/database-config</div>
            <p><i>This user was created dynamically by Vault!</i></p>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    # Starts the Flask development server on all interfaces at port 5000.
    app.run(host='0.0.0.0', port=5000)
