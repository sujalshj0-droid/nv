import os
import time
import threading
from flask import Flask, render_template, request, jsonify
from instagrapi import Client

app = Flask(__name__)

running = False
status_log = "System Ready"

def change_name_loop(session_id, names_list, thread_id, delay, break_after, break_duration):
    global running, status_log
    cl = Client()
    
    try:
        status_log = "Logging in via Session ID..."
        # Use a consistent user agent to avoid triggering security blocks
        cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x1920; Xiaomi/Redmi; Redmi Note 8 Pro; begonia; en_US; 332306352)")
        
        # Log in using the session ID provided
        cl.login_by_sessionid(session_id)
        
        # REMOVED: cl.get_timeline_feed() -> This was causing the 400 error in your screenshot
        
        # Basic check to see if the session is alive without a full feed pull
        user_info = cl.user_info(cl.user_id)
        status_log = f"Logged in as @{user_info.username}. Starting loop..."
        
    except Exception as e:
        status_log = f"Login Error: {str(e)}"
        running = False
        return

    change_count = 0
    while running:
        for name in names_list:
            if not running: break
            
            clean_name = name.strip()
            if not clean_name: continue

            try:
                # Rename the thread using the provided Thread ID
                cl.direct_thread_rename(thread_id, clean_name)
                change_count += 1
                status_log = f"Changed to: {clean_name} | Total: {change_count}"
                
                # Handling the Break logic
                if change_count % break_after == 0:
                    status_log = f"Safety break: Resting for {break_duration}s..."
                    time.sleep(break_duration)
                else:
                    time.sleep(delay)
                    
            except Exception as e:
                # If Instagram blocks the action, wait longer
                status_log = f"Action Blocked/Error: Waiting 2 mins. ({str(e)})"
                time.sleep(120)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global running
    if not running:
        data = request.json
        names = data.get('names', '').split(',')
        sid = data.get('sid')
        tid = data.get('tid')
        delay = int(data.get('delay', 60))
        break_after = int(data.get('break_after', 10))
        break_duration = int(data.get('break_duration', 300))
        
        running = True
        thread = threading.Thread(target=change_name_loop, args=(sid, names, tid, delay, break_after, break_duration))
        thread.daemon = True # Ensures thread closes if the app stops
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
