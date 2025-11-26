import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai.preview import reasoning_engines

from adk_short_bot.agent import root_agent

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("user_id", "test_user", "User ID for session operations.")
flags.DEFINE_string("session_id", None, "Session ID for operations.")
flags.DEFINE_string(
    "message",
    "Shorten this message: Hello, how are you doing today?",
    "Message to send to the agent.",
)
flags.DEFINE_bool("create_session", False, "Creates a new session.")
flags.DEFINE_bool("list_sessions", False, "Lists all sessions for a user.")
flags.DEFINE_bool("get_session", False, "Gets a specific session.")
flags.DEFINE_bool("send", False, "Sends a message to the local agent.")
flags.mark_bool_flags_as_mutual_exclusive(
    ["create_session", "list_sessions", "get_session", "send"]
)


def _init_app():
    load_dotenv()

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION")

    if not project_id:
        print("Missing required environment variable: GOOGLE_CLOUD_PROJECT")
        sys.exit(1)
    if not location:
        print("Missing required environment variable: GOOGLE_CLOUD_LOCATION")
        sys.exit(1)

    print(f"Initializing Vertex AI with project={project_id}, location={location}")
    vertexai.init(project=project_id, location=location)

    print("Creating local app instance...")
    return reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)


def _create_session(app_instance):
    session = app_instance.create_session(
        user_id=FLAGS.user_id, session_id=FLAGS.session_id
    )
    print("Session created:")
    print(f"  Session ID: {session.id}")
    print(f"  User ID: {session.user_id}")
    print(f"  App name: {session.app_name}")
    return session


def _list_sessions(app_instance):
    sessions = app_instance.list_sessions(user_id=FLAGS.user_id)
    print(f"Sessions for user '{FLAGS.user_id}':")
    if hasattr(sessions, "sessions"):
        print(sessions.sessions)
    elif hasattr(sessions, "session_ids"):
        print(sessions.session_ids)
    else:
        print(sessions)


def _get_session(app_instance):
    if not FLAGS.session_id:
        print("session_id is required for get_session")
        sys.exit(1)
    session = app_instance.get_session(
        user_id=FLAGS.user_id, session_id=FLAGS.session_id
    )
    print("Session details:")
    print(f"  ID: {session.id}")
    print(f"  User ID: {session.user_id}")
    print(f"  App name: {session.app_name}")
    print(f"  Last update time: {session.last_update_time}")
    return session


def _send_message(app_instance):
    message = FLAGS.message
    session_id = FLAGS.session_id
    user_id = FLAGS.user_id

    session = None
    if session_id:
        try:
            session = app_instance.get_session(user_id=user_id, session_id=session_id)
        except Exception:
            # If the session does not exist yet in this local app, create one with the given ID.
            session = app_instance.create_session(user_id=user_id, session_id=session_id)
    else:
        session = app_instance.create_session(user_id=user_id)
        session_id = session.id

    print(f"Sending message to session {session_id}:")
    print(f"Message: {message}")
    print("\nResponse:")
    for event in app_instance.stream_query(
        user_id=user_id, session_id=session_id, message=message
    ):
        print(event)


def main(argv=None):
    if argv is None:
        argv = flags.FLAGS(sys.argv)
    else:
        argv = flags.FLAGS(argv)

    app_instance = _init_app()

    if FLAGS.create_session:
        _create_session(app_instance)
    elif FLAGS.list_sessions:
        _list_sessions(app_instance)
    elif FLAGS.get_session:
        _get_session(app_instance)
    elif FLAGS.send:
        _send_message(app_instance)
    else:
        # Default behaviour mirrors the old script for quick smoke tests.
        session = _create_session(app_instance)
        print("\nListing sessions...")
        _list_sessions(app_instance)
        print("\nSending test query...")
        FLAGS.session_id = session.id
        _send_message(app_instance)


if __name__ == "__main__":
    app.run(main)
