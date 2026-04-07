import os
import time
import threading
from flask import Flask, render_template, request, jsonify
from instagrapi import Client

app = Flask(__name__)

# Global variables to control the loop
running = False
status_log = "System Ready"

def change_name_loop(session_id, names_list, thread_id, delay, break_after, break_duration):
    global running, status_log
    cl = Client()
    
    try:
        status_log = "Attempting Login..."
        # We set a custom user agent to reduce 'login_required' errors
        cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x1920; Xiaomi/Redmi; Redmi Note 8 Pro; begonia; en_US; 332306352)")
        cl.login_by_sessionid(session_id)
        
        # Verify the session
        cl.get_timeline_feed() 
        status_log = f"Connected to Thread: {thread_id}"
    except Exception as e:
        status_log = f"Login Error: {str(e)}"
        running = False
        return

    change_count = 0
    while running:
        for name in names_list:
            if not running: break
            
            name = name.strip()
            if not name: continue

            try:
                # Direct API call to change group thread title
                cl.direct_thread_rename(thread_id, name)
                change_count += 1
                status_log = f"Success: {name} (Total: {change_count})"
                
                # Check for Break logic
                if change_count % break_after == 0:
                    status_log = f"Taking safety break for {break_duration}s..."
                    time.sleep(break_duration)
                else:
                    time.sleep(delay)
                    
            except Exception as e:
                status_log = f"Loop Error: {str(e)}"
                # If we hit an error, wait 60s before trying the next name
                time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global running
    if not running:
        data = request.json
        # Inputs from the new frontend
        names = data.get('names', '').split(',')
        sid = data.get('sid')
        tid = data.get('tid') # Thread ID
        delay = int(data.get('delay', 60))
        break_after = int(data.get('break_after', 5))
        break_duration = int(data.get('break_duration', 600))
        
        running = True
        thread = threading.Thread(target=change_name_loop, args=(sid, names, tid, delay, break_after, break_duration))
        thread.start()
        return jsonify({"status": "Started"})
    return jsonify({"status": "Already running"})

@app.route('/stop', methods=['POST'])
def stop():
    global running
    running = False
    return jsonify({"status": "Stopped"})

@app.route('/status')
def status():
    return jsonify({"log": status_log, "running": running})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
