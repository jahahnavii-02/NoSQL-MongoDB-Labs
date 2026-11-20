import json
import os

import requests
import streamlit as st

API = os.getenv("THREATSENTRY_API", "http://127.0.0.1:8000")
MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")

st.set_page_config(page_title="ThreatSentry AI", page_icon="🛡️", layout="wide")
st.title("🛡️ ThreatSentry AI")
st.caption("Threat intelligence for Linux, Windows, macOS, Android and iOS — with confirmation-based Linux mitigation")

if "messages" not in st.session_state:
    st.session_state.messages = []


def post(path, **kw):
    r = requests.post(f"{API}{path}", timeout=kw.pop("timeout", 30), **kw)
    r.raise_for_status()
    return r.json()


def token_stream(prompt, holder):
    """Yield answer text as it arrives from the backend (keeps the browser connection alive)."""
    try:
        with requests.post(f"{API}/api/chat/stream", stream=True, timeout=(10, 600),
                           json={"message": prompt, "conversation_id": st.session_state.get("conversation_id")}) as r:
            r.raise_for_status()
            for raw in r.iter_lines():
                if not raw:
                    continue
                d = json.loads(raw.decode("utf-8"))
                if "conversation_id" in d:
                    holder["cid"] = d["conversation_id"]
                if "error" in d:
                    yield f"\n\n⚠️ {d['error']}"
                if "token" in d:
                    yield d["token"]
    except requests.RequestException as exc:
        yield f"\n\n⚠️ Could not reach the chat service: {exc}"


with st.sidebar:
    st.subheader("Conversations")
    if st.button("＋ New conversation", use_container_width=True):
        st.session_state.pop("conversation_id", None)
        st.session_state.messages = []
        st.rerun()
    try:
        for item in requests.get(f"{API}/api/chat/conversations", timeout=10).json().get("conversations", []):
            cid = item.get("conversation_id")
            if st.button(item.get("title", "Conversation")[:45], key=cid, use_container_width=True):
                st.session_state.conversation_id = cid
                msgs = requests.get(f"{API}/api/chat/conversations/{cid}/messages", timeout=10).json()["messages"]
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                st.rerun()
    except requests.RequestException:
        st.caption("Conversation history unavailable.")

    st.divider()
    st.subheader("Linux scan")
    if st.button("Run read-only scan", use_container_width=True):
        with st.spinner("Scanning installed packages..."):
            try:
                s = post("/api/scans/linux", timeout=300)["summary"]
                st.success(f"Affected: {s['affected_version_matches']} · Unknown: {s['version_assessment_unknown']} · "
                           f"Not affected: {s['not_affected_matches']}")
            except requests.RequestException as exc:
                st.error(f"Scan failed: {exc}")

    st.subheader("Mitigation plans")
    try:
        data = requests.get(f"{API}/api/mitigations/", timeout=10).json()
        st.caption("Mode: DRY RUN (no changes)" if data["dry_run"] else "Mode: LIVE — approved fixes are applied")
        for p in data["plans"][:8]:
            st.markdown(f"**{p['plan_id'][:8]}** · {p['package']} · `{p['status']}`  \n`{p['command']}`")
            if p["status"] == "proposed":
                c1, c2 = st.columns(2)
                if c1.button("Approve", key="a" + p["plan_id"]):
                    st.session_state.messages.append(
                        {"role": "assistant", "content": post(f"/api/mitigations/{p['plan_id'][:8]}/approve")["result"]})
                    st.rerun()
                if c2.button("Reject", key="r" + p["plan_id"]):
                    post(f"/api/mitigations/{p['plan_id'][:8]}/reject")
                    st.rerun()
        if not data["plans"]:
            st.caption("None yet. Run a scan, then type e.g. `fix openssl` in the chat.")
    except requests.RequestException:
        st.caption("Plans unavailable.")

    st.divider()
    st.caption(f"Local model: {MODEL}")
    st.caption("Storage: MongoDB · No change without your approval")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask anything: 'active Windows threats', 'how does ransomware spread?', 'fix openssl'...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        note = st.empty()
        note.caption("Thinking… the first words can take up to a minute on a CPU-only model.")
        holder = {}
        answer = st.write_stream(token_stream(prompt, holder))
        note.empty()
    if holder.get("cid"):
        st.session_state.conversation_id = holder["cid"]
    st.session_state.messages.append({"role": "assistant", "content": answer})
