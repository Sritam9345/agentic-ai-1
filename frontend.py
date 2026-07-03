
import streamlit as st
from uuid import uuid4

from graph.graph_logic import (
    get_initial_state,
    stream_graph,
    stream_resume_graph,
)

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Trip Planner Agent",
    page_icon="🧳",
    layout="wide"
)

st.title("🧳 LangGraph Trip Planner")
st.caption(
    "Planner + Destination + Weather + Transport + Budget + Itinerary Agents"
)

# ==================================================
# SESSION STATE
# ==================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())

if "state" not in st.session_state:
    st.session_state.state = get_initial_state()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "waiting_for_interrupt" not in st.session_state:
    st.session_state.waiting_for_interrupt = False


# ==================================================
# HELPERS
# ==================================================

def extract_interrupt_payload(interrupt_data) -> dict:
    """
    Normalizes whatever LangGraph hands back for an interrupt into a plain
    dict, e.g. {"question": "...", "reason": "..."}.

    LangGraph typically returns this as a list/tuple of Interrupt objects,
    each with a `.value` attribute holding the dict passed to interrupt(...).
    This unwraps that so the frontend never renders a raw Python repr.
    """
    payload = None

    if isinstance(interrupt_data, (list, tuple)) and interrupt_data:
        first = interrupt_data[0]
        payload = getattr(first, "value", first)
    else:
        payload = interrupt_data

    if not isinstance(payload, dict):
        payload = {"question": str(payload)}

    return payload


def render_interrupt(interrupt_data):
    """Displays the HITL question cleanly, with any extra context tucked
    into an expander instead of dumping the raw interrupt dict."""

    payload = extract_interrupt_payload(interrupt_data)

    question = payload.get("question") or (
        "The planner needs a bit more information before continuing."
    )

    interrupt_text = f"🤔 {question}"
    st.markdown(interrupt_text)

    extra_context = {
        k: v for k, v in payload.items()
        if k != "question" and v
    }

    if extra_context:
        with st.expander("Why is the agent asking this?"):
            if "reason" in extra_context:
                st.write(extra_context["reason"])

            if "current_results" in extra_context:
                st.caption("Results gathered so far:")
                st.json(extra_context["current_results"])

            for key, value in extra_context.items():
                if key not in ("reason", "current_results"):
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    return interrupt_text


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.header("Controls")

    st.write("Thread ID")
    st.code(st.session_state.thread_id)

    if st.button("Reset Conversation"):

        st.session_state.thread_id = str(uuid4())
        st.session_state.state = get_initial_state()
        st.session_state.chat_history = []
        st.session_state.waiting_for_interrupt = False

        st.rerun()


# ==================================================
# DISPLAY CHAT HISTORY
# ==================================================

for msg in st.session_state.chat_history:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ==================================================
# CHAT INPUT
# ==================================================

user_input = st.chat_input(
    "Tell me your travel plan..."
)

# ==================================================
# HANDLE USER MESSAGE
# ==================================================

if user_input:

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    st.session_state.user_query = user_input

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        # ----------------------------------
        # LIVE AGENT PROGRESS
        # ----------------------------------

        status_box = st.status(
            "Starting agent workflow...",
            expanded=True,
        )

        agents_seen = []

        try:

            # ----------------------------------
            # RESUME FROM INTERRUPT vs NEW EXECUTION
            # ----------------------------------

            if st.session_state.waiting_for_interrupt:

                event_stream = stream_resume_graph(
                    user_input=user_input,
                    thread_id=st.session_state.thread_id
                )

                st.session_state.waiting_for_interrupt = False

            else:

                event_stream = stream_graph(
                    state=st.session_state.state,
                    user_input=user_input,
                    thread_id=st.session_state.thread_id
                )

            # ----------------------------------
            # CONSUME STREAM, SHOWING EACH AGENT AS IT RUNS
            # ----------------------------------

            result = {}

            for event in event_stream:

                node = event["node"]

                if node == "__final__":
                    result = event.get("final_state", {})
                    break

                label = event["label"]

                if label not in agents_seen:
                    agents_seen.append(label)
                    status_box.write(f"▶️ {label}")

                status_box.update(label=f"Running: {label}")

            status_box.update(
                label="✅ Agent workflow completed",
                state="complete",
            )

            # ----------------------------------
            # UPDATE GRAPH STATE
            # ----------------------------------

            if isinstance(result, dict):
                st.session_state.state.update(result)

            # ----------------------------------
            # INTERRUPT
            # ----------------------------------

            if "__interrupt__" in result:

                interrupt_data = result["__interrupt__"]

                st.session_state.waiting_for_interrupt = True

                status_box.update(
                    label="⏸️ Waiting for your input",
                    state="complete",
                )

                interrupt_text = render_interrupt(interrupt_data)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": interrupt_text
                    }
                )

            # ----------------------------------
            # FINAL ITINERARY
            # ----------------------------------

            elif result.get("itinerary"):

                itinerary = result["itinerary"]

                if agents_seen:
                    st.caption("Agents involved: " + " → ".join(agents_seen))

                st.markdown("### ✈️ Final Itinerary")
                st.markdown(itinerary)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": itinerary
                    }
                )

            # ----------------------------------
            # INTERMEDIATE RESULTS
            # ----------------------------------

            elif result.get("results"):

                response = "✅ Planning step completed."

                if agents_seen:
                    st.caption("Agents involved: " + " → ".join(agents_seen))

                st.markdown(response)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response
                    }
                )

                with st.expander("Agent Results"):

                    st.json(
                        result.get(
                            "results",
                            {}
                        )
                    )

            # ----------------------------------
            # GENERIC RESPONSE
            # ----------------------------------

            else:

                response = "✅ Graph execution completed."

                if agents_seen:
                    st.caption("Agents involved: " + " → ".join(agents_seen))

                st.markdown(response)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response
                    }
                )

        except Exception as e:

            status_box.update(
                label="❌ Agent workflow failed",
                state="error",
            )

            error_message = f"❌ {str(e)}"

            st.error(error_message)

            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": error_message
                }
            )


# ==================================================
# DEBUG PANEL
# ==================================================

with st.expander("Current Graph State"):

    st.json(st.session_state.state)