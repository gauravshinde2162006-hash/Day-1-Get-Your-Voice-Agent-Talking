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
                <title>Escalations Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    h1 { color: #333; }
                </style>
            </head>
            <body>
                <h1>Active Escalations</h1>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Who</th>
                        <th>What</th>
                        <th>Checked</th>
                        <th>Urgency</th>
                        <th>Lang/Follow-up</th>
                        <th>Status</th>
                        <th>Created At</th>
                    </tr>
            """
            
            try:
                # Ensure DB exists
                db_path = "users.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Check if escalations table exists
                    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='escalations'")
                    if cursor.fetchone()[0] == 1:
                        cursor.execute("SELECT id, who, what, checked, urgency, language_and_follow_up, status, created_at FROM escalations ORDER BY created_at DESC")
                        rows = cursor.fetchall()
                        if rows:
                            for row in rows:
                                html += "<tr>"
                                for col in row:
                                    html += f"<td>{str(col)}</td>"
                                html += "</tr>"
                        else:
                            html += "<tr><td colspan='8'>No escalations found.</td></tr>"
                    else:
                        html += "<tr><td colspan='8'>Escalations table does not exist yet. Run the agent first.</td></tr>"
                    conn.close()
                else:
                    html += "<tr><td colspan='8'>Database not found.</td></tr>"
            except Exception as e:
                html += f"<tr><td colspan='8'>Error loading data: {e}</td></tr>"

            html += """
                </table>
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
