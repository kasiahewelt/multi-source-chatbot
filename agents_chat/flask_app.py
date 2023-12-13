from flask import Flask, render_template, request, session, redirect, url_for
from orchestrator import get_response, SYSTEM_PROMPT
import psycopg2
import uuid
import secrets
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = secrets.token_hex(16)

HISTORY_TOKEN_LIMIT = 6_000
MAX_CONVERSATIONS = 5
MAX_RETRIES = 3
CONVERSATIONS = {}
MESSAGES = {}


def trim_history(messages):
    messages.pop(1)
    while messages[1]["role"] != "user" and len(messages) > 1:
        messages.pop(1)


def handle_query(query, session_id):
    response = ""
    if query:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                response, total_tokens = get_response(query, MESSAGES[session_id])
                logger.info(f"Whole conversation has {total_tokens=}")
                if total_tokens > HISTORY_TOKEN_LIMIT:
                    trim_history(MESSAGES[session_id])
                    logger.info(f"Conversation was longer that {HISTORY_TOKEN_LIMIT}. Trimmed it down")
                break
            except psycopg2.OperationalError:
                response = "Database connection error. Please try again."
                logger.exception("DataBase error")
                retries += 1
                if retries == MAX_RETRIES:
                    response += " Max retries reached. Please ask your question again."
            except Exception as e:
                response = "An error occurred. Please ask your question again or rephrase your question."
                logger.exception("Exception error")
                break

        if not response:
            response = "An error occurred. Please ask your question again."

        CONVERSATIONS[session_id].append((query, response))
        if len(CONVERSATIONS[session_id]) > MAX_CONVERSATIONS:
            CONVERSATIONS[session_id].pop(0)  # Remove the oldest conversation


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'session_id' not in session:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        CONVERSATIONS[session_id] = []
        MESSAGES[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    session_id = session['session_id']

    if request.method == 'POST':
        query = request.form.get('query')
        handle_query(query, session_id)

    return render_template('index.html', conversations=CONVERSATIONS[session_id])


@app.route('/clear_session', methods=['POST'])
def clear_session():
    session_id = session.pop("session_id")
    CONVERSATIONS.pop(session_id)
    MESSAGES.pop(session_id)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=os.environ['SRV_PORT'], host='0.0.0.0')
