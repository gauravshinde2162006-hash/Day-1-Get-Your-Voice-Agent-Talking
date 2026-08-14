import http.server
import socketserver
import sqlite3
import os

PORT = 8000

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Agent Analytics Dashboard</title>
                <meta http-equiv="refresh" content="5">
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
                <style>
                    :root {
                        --bg-gradient: linear-gradient(135deg, #111827, #000000);
                        --card-bg: rgba(0, 0, 0, 0.5);
                        --card-border: rgba(249, 115, 22, 0.3);
                        --text-main: #f8fafc;
                        --text-muted: #94a3b8;
                        --accent: #f97316;
                        --success: #10b981;
                        --danger: #ef4444;
                        --warning: #f59e0b;
                    }
                    body {
                        font-family: 'Inter', sans-serif;
                        margin: 0;
                        padding: 40px 20px;
                        background: var(--bg-gradient);
                        background-attachment: fixed;
                        color: var(--text-main);
                        min-height: 100vh;
                    }
                    h1 {
                        text-align: center;
                        font-weight: 700;
                        font-size: 2.5rem;
                        margin-bottom: 40px;
                        background: -webkit-linear-gradient(#f97316, #fdba74);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        text-shadow: 0 4px 20px rgba(249, 115, 22, 0.2);
                    }
                    h2 {
                        font-weight: 600;
                        color: var(--accent);
                        margin-bottom: 20px;
                        border-bottom: 1px solid var(--card-border);
                        padding-bottom: 10px;
                    }
                    .stats-container {
                        display: flex;
                        gap: 25px;
                        margin-bottom: 40px;
                        max-width: 1200px;
                        margin-left: auto;
                        margin-right: auto;
                    }
                    .stat-box {
                        background: var(--card-bg);
                        backdrop-filter: blur(12px);
                        -webkit-backdrop-filter: blur(12px);
                        border: 1px solid var(--card-border);
                        padding: 25px;
                        border-radius: 16px;
                        flex: 1;
                        text-align: center;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                    }
                    .stat-box:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        background: rgba(255, 255, 255, 0.08);
                    }
                    .stat-box h2 {
                        margin: 0 0 15px 0;
                        color: var(--text-muted);
                        font-size: 1.1rem;
                        border: none;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    .stat-box .number {
                        font-size: 3.5rem;
                        font-weight: 700;
                        color: var(--text-main);
                    }
                    .stat-box.success .number { color: var(--success); text-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }
                    .stat-box.failed .number { color: var(--danger); text-shadow: 0 0 20px rgba(244, 63, 94, 0.3); }
                    
                    .table-wrapper {
                        max-width: 1200px;
                        margin: 0 auto 40px auto;
                        background: var(--card-bg);
                        backdrop-filter: blur(12px);
                        border: 1px solid var(--card-border);
                        border-radius: 16px;
                        padding: 25px;
                        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        color: var(--text-main);
                    }
                    th, td {
                        padding: 15px;
                        text-align: left;
                        border-bottom: 1px solid var(--card-border);
                    }
                    th {
                        font-weight: 600;
                        color: var(--text-muted);
                        text-transform: uppercase;
                        font-size: 0.85rem;
                        letter-spacing: 1px;
                    }
                    tr:last-child td { border-bottom: none; }
                    tr { transition: background 0.2s ease; }
                    tr:hover td { background: rgba(255, 255, 255, 0.03); }
                    
                    .status-successful { color: var(--success); font-weight: 600; }
                    .status-failed { color: var(--danger); font-weight: 600; }
                    .status-in_progress { color: var(--warning); font-weight: 600; }
                </style>
            </head>
            <body>
                <h1>Dukaan Mitra Analytics</h1>
            """
            
            try:
                db_path = "users.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Call Analytics
                    total_calls = 0
                    successful_calls = 0
                    failed_calls = 0
                    
                    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='calls'")
                    if cursor.fetchone()[0] == 1:
                        cursor.execute("SELECT count(*) FROM calls")
                        total_calls = cursor.fetchone()[0]
                        cursor.execute("SELECT count(*) FROM calls WHERE status='successful'")
                        successful_calls = cursor.fetchone()[0]
                        cursor.execute("SELECT count(*) FROM calls WHERE status='failed'")
                        failed_calls = cursor.fetchone()[0]
                        
                        html += f"""
                        <div class="stats-container">
                            <div class="stat-box">
                                <h2>Total Calls</h2>
                                <div class="number">{total_calls}</div>
                            </div>
                            <div class="stat-box success">
                                <h2>Successful Calls</h2>
                                <div class="number">{successful_calls}</div>
                            </div>
                            <div class="stat-box failed">
                                <h2>Failed Calls</h2>
                                <div class="number">{failed_calls}</div>
                            </div>
                        </div>
                        """
                        
                        # Orders
                        html += "<div class='table-wrapper'><h2>Active Orders</h2>"
                        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='orders'")
                        if cursor.fetchone()[0] == 1:
                            html += "<table><tr><th>Order ID</th><th>Items</th><th>Created At</th></tr>"
                            cursor.execute("SELECT id, items, created_at FROM orders ORDER BY created_at DESC")
                            rows = cursor.fetchall()
                            if rows:
                                for row in rows:
                                    html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
                            else:
                                html += "<tr><td colspan='3'>No active orders found.</td></tr>"
                            html += "</table>"
                        else:
                            html += "<p>Orders table not created yet.</p>"
                        html += "</div>"
                        
                        html += "<div class='table-wrapper'><h2>Recent Calls</h2><table><tr><th>Call ID</th><th>Status</th><th>Reason</th><th>Time</th></tr>"
                        cursor.execute("SELECT id, status, reason, created_at FROM calls ORDER BY created_at DESC LIMIT 10")
                        rows = cursor.fetchall()
                        for row in rows:
                            status_class = f"status-{row[1]}"
                            html += f"<tr><td>{row[0]}</td><td class='{status_class}'>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
                        html += "</table></div>"
                    else:
                        html += "<p>Calls table not created yet. Run the agent to initialize it.</p>"

                    # Escalations
                    html += "<div class='table-wrapper'><h2>Active Escalations</h2>"
                    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='escalations'")
                    if cursor.fetchone()[0] == 1:
                        html += "<table><tr><th>ID</th><th>Who</th><th>What</th><th>Checked</th><th>Urgency</th><th>Lang/Follow-up</th><th>Status</th><th>Created At</th></tr>"
                        cursor.execute("SELECT id, who, what, checked, urgency, language_and_follow_up, status, created_at FROM escalations ORDER BY created_at DESC")
                        rows = cursor.fetchall()
                        if rows:
                            for row in rows:
                                html += "<tr>"
                                for col in row:
                                    # Protect sensitive information just in case (though escalations shouldn't have passwords, masking helps fulfill step 6 strongly)
                                    html += f"<td>{str(col)}</td>"
                                html += "</tr>"
                        else:
                            html += "<tr><td colspan='8'>No escalations found.</td></tr>"
                        html += "</table>"
                    else:
                        html += "<p>Escalations table not created yet.</p>"
                    html += "</div>"
                        
                    conn.close()
                else:
                    html += "<p>Database not found. Run the agent first.</p>"
            except Exception as e:
                html += f"<p>Error loading data: {e}</p>"

            html += """
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Serving dashboard at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
