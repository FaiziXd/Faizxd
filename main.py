from flask import Flask, jsonify, render_template_string, request
import requests
import time
import threading

app = Flask(__name__)

# Global variable to control message sending
send_messages_flag = True

# Function to send a message to a Facebook group
def send_facebook_message(access_token, group_id, message):
    url = f"https://graph.facebook.com/v12.0/{group_id}/messages"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {"text": message}
    }
    
    params = {
        "access_token": access_token
    }

    response = requests.post(url, headers=headers, json=payload, params=params)
    return response.status_code, response.text

# Function to handle sending messages in a separate thread
def send_messages_thread(group_ids, messages, access_tokens, speed):
    global send_messages_flag

    for group_id in group_ids:
        if not send_messages_flag:
            break
        for access_token in access_tokens:
            message = messages.get(group_id, "")
            if message:
                status_code, response_text = send_facebook_message(access_token, group_id, message)
                print(f"Sent to {group_id} using token {access_token}: {status_code}, {response_text}")
                time.sleep(speed)  # Use the specified speed

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Message Sender</title>
        <style>
            body {
                background-image: url('https://iili.io/2K2zDZb.jpg');
                background-size: cover;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
            }
            .form-container {
                background: rgba(0, 0, 0, 0.7);
                padding: 30px;
                border-radius: 10px;
                display: inline-block;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
            }
            input[type="text"], input[type="number"] {
                width: 80%;
                padding: 10px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
            }
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                background-color: #007bff;
                color: white;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
            h1 {
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.7);
            }
            .highlight {
                background-color: yellow;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1 class="highlight">Message Sender</h1>
        <div class="form-container">
            <form id="messageForm">
                <input type="text" name="access_token" placeholder="Enter Access Token" required>
                <div id="groupInputs">
                    <input type="text" name="group_id" placeholder="Enter Group UID" required>
                    <input type="text" name="message" placeholder="Enter Message" required>
                </div>
                <button type="button" onclick="addGroup()">Add Another Group</button>
                <input type="number" name="speed" placeholder="Speed (seconds)" required min="1>
                <button type="submit">Send Messages</button>
            </form>
            <div id="status"></div>
        </div>
        <script>
            let groupCount = 1;

            function addGroup() {
                if (groupCount < 10) {
                    groupCount++;
                    const div = document.createElement('div');
                    div.innerHTML = `<input type="text" name="group_id" placeholder="Enter Group UID" required>
                                     <input type="text" name="message" placeholder="Enter Message" required>`;
                    document.getElementById('groupInputs').appendChild(div);
                }
            }

            document.getElementById('messageForm').onsubmit = function(event) {
                event.preventDefault();
                const formData = new FormData(this);
                const data = {};
                formData.forEach((value, key) => {
                    if (!data[key]) {
                        data[key] = [];
                    }
                    data[key].push(value);
                });

                const payload = data['group_id'].map((id, index) => {
                    return { id, message: data['message'][index] };
                });

                const accessTokens = data['access_token'];
                const speed = parseInt(data['speed'][0], 10);  // Get speed input

                // Start sending messages in a separate thread
                fetch('/send_messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ access_token: accessTokens, messages: payload, speed: speed })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerText = data.status;
                });
            };
        </script>
    </body>
    </html>
    '''

@app.route('/send_messages', methods=['POST'])
def send_messages():
    global send_messages_flag
    send_messages_flag = True  # Allow sending messages

    content = request.json
    access_tokens = content['access_token']
    group_ids = [g['id'] for g in content['messages']]
    messages = {g['id']: g['message'] for g in content['messages']}
    speed = content['speed']  # Get the speed from the request

    # Start the message sending thread
    threading.Thread(target=send_messages_thread, args=(group_ids, messages, access_tokens, speed)).start()

    return jsonify({"status": "Messages are being sent!"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)
    
