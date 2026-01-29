# В разделе HTTP сервера обновите HealthHandler:

class HealthHandler(BaseHTTPRequestHandler):
    """Обработчик health check запросов для Render и HetrixTools"""
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            import datetime
            import psutil
            import os
            
            # Получаем информацию о системе
            process = psutil.Process(os.getpid())
            uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())
            uptime_str = str(uptime).split('.')[0]
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            response_text = (
                "OK\n"
                f"Service: Energy Telegram Bot\n"
                f"Status: Active\n"
                f"Uptime: {uptime_str}\n"
                f"Memory: {memory_mb:.1f} MB\n"
                f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Hosting: Render.com\n"
                f"Monitoring: HetrixTools"
            )
            
            self.wfile.write(response_text.encode('utf-8'))
            
        elif self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'PONG')
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')