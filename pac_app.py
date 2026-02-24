import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import json
import re

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PAC – Personnel Advisory Committee",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── SUPABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ─── STYLES ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #f8f6f0; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }

/* Header */
.pac-header {
    background: linear-gradient(135deg, #1a2e4a 0%, #2d4a6e 60%, #3a5f8a 100%);
    color: white;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    box-shadow: 0 4px 20px rgba(26,46,74,0.25);
}
.pac-header-icon { font-size: 3rem; }
.pac-header-text h1 { margin: 0; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; }
.pac-header-text p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.95rem; }

/* Meeting cards */
.meeting-card {
    background: white;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.75rem;
    border-left: 5px solid #1a2e4a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    cursor: pointer;
    transition: box-shadow 0.2s;
}
.meeting-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.12); }
.meeting-card.draft { border-left-color: #f59e0b; }
.meeting-card.open { border-left-color: #3b82f6; }
.meeting-card.finalised { border-left-color: #10b981; }
.meeting-card.upcoming { border-left-color: #8b5cf6; }

.meeting-card h3 { margin: 0 0 0.25rem; font-size: 1.05rem; color: #1a2e4a; }
.meeting-card .meta { font-size: 0.82rem; color: #666; display: flex; gap: 1.2rem; flex-wrap: wrap; }
.status-badge {
    display: inline-block; padding: 0.2rem 0.65rem;
    border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.badge-upcoming { background: #ede9fe; color: #6d28d9; }
.badge-open { background: #dbeafe; color: #1d4ed8; }
.badge-draft { background: #fef3c7; color: #92400e; }
.badge-finalised { background: #d1fae5; color: #065f46; }

/* Section headers */
.section-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.section-card h2 {
    margin: 0 0 1rem;
    font-size: 1.1rem;
    color: #1a2e4a;
    border-bottom: 2px solid #e8e4d9;
    padding-bottom: 0.5rem;
}

/* Agenda items */
.agenda-item {
    background: #f8f6f0;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    border-left: 3px solid #d4af37;
}
.agenda-item h4 { margin: 0 0 0.2rem; font-size: 0.95rem; color: #1a2e4a; }
.agenda-item p { margin: 0; font-size: 0.85rem; color: #555; }
.agenda-item .submitter { font-size: 0.78rem; color: #888; margin-top: 0.3rem; }

/* Action items */
.action-item {
    background: #fff8f0;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    border-left: 3px solid #f59e0b;
}
.action-done { background: #f0fdf4; border-left-color: #10b981; }

/* Attendance */
.attend-row {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.5rem 0; border-bottom: 1px solid #f0ede6;
}

/* Minutes */
.minutes-box {
    background: #fafaf8;
    border: 1px solid #e2ddd3;
    border-radius: 8px;
    padding: 1.2rem;
    white-space: pre-wrap;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #333;
}

/* Divider */
hr { border: none; border-top: 1px solid #e8e4d9; margin: 1rem 0; }

/* Buttons */
.stButton>button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.15s;
}
.stDownloadButton>button { border-radius: 8px; }

/* Info boxes */
.info-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.88rem;
    color: #1e40af;
    margin-bottom: 1rem;
}
.warn-box {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.88rem;
    color: #92400e;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ─── DB HELPERS ─────────────────────────────────────────────────────────────────

def db_meetings():
    return supabase.table("pac_meetings").select("*").order("meeting_date", desc=True).execute().data

def db_meeting(mid):
    r = supabase.table("pac_meetings").select("*").eq("id", mid).execute().data
    return r[0] if r else None

def db_agenda(mid):
    return supabase.table("pac_agenda_items").select("*").eq("meeting_id", mid).order("order_no").execute().data

def db_attendance(mid):
    return supabase.table("pac_attendance").select("*").eq("meeting_id", mid).order("staff_name").execute().data

def db_minutes(mid):
    r = supabase.table("pac_minutes").select("*").eq("meeting_id", mid).execute().data
    return r[0] if r else None

def db_actions(mid):
    return supabase.table("pac_action_items").select("*").eq("meeting_id", mid).order("created_at").execute().data

def db_docs(mid):
    return supabase.table("pac_documents").select("*").eq("meeting_id", mid).order("created_at").execute().data

def fmt_date(d):
    if not d:
        return "—"
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%-d %B %Y")
    except:
        return str(d)[:10]

# ─── ADMIN CHECK ────────────────────────────────────────────────────────────────
def check_admin():
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    return st.session_state.is_admin

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pac-header">
  <div class="pac-header-icon">🏛️</div>
  <div class="pac-header-text">
    <h1>Personnel Advisory Committee</h1>
    <p>Cowandilla Learning Centre — Meeting Agendas, Minutes &amp; Actions</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Admin Access")
    if not check_admin():
        pw = st.text_input("Admin password", type="password", key="admin_pw")
        if st.button("Sign in", use_container_width=True):
            admin_pass = st.secrets.get("PAC_ADMIN_PASSWORD", "PAC2026")
            if pw == admin_pass:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        st.success("✅ Admin mode active")
        if st.button("Sign out", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    st.markdown("---")
    st.markdown("### 📌 About PAC")
    st.markdown("""
The **Personnel Advisory Committee** operates under DfE and CLC policy requirements.

**All staff** can:
- Submit agenda items
- View agendas & minutes
- Track action items

**Admin** can:
- Schedule meetings
- Record & finalise minutes
- Manage attendance
- Add supporting documents
    """)

# ─── NAVIGATION ─────────────────────────────────────────────────────────────────
tab_all, tab_upcoming, tab_actions = st.tabs(["📅 All Meetings", "⏭ Upcoming Meetings", "✅ Action Register"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 – ALL MEETINGS
# ════════════════════════════════════════════════════════════════════════════════
with tab_all:
    # Create new meeting (admin only)
    if check_admin():
        with st.expander("➕ Schedule a New Meeting", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                new_date = st.date_input("Meeting date", value=date.today() + timedelta(days=14), key="nm_date")
                new_time = st.time_input("Start time", value=datetime.strptime("09:30", "%H:%M").time(), key="nm_time")
            with col2:
                new_loc = st.text_input("Location", value="LBU Meeting Room", key="nm_loc")
                new_chair = st.text_input("Chair", key="nm_chair")
            new_type = st.selectbox("Meeting type", ["Ordinary", "Special", "Annual"], key="nm_type")
            new_notice = st.text_area("Notice / Agenda preamble (optional)", key="nm_notice")
            if st.button("📅 Create Meeting", type="primary", use_container_width=True):
                if new_chair.strip():
                    supabase.table("pac_meetings").insert({
                        "meeting_date": str(new_date),
                        "start_time": str(new_time),
                        "location": new_loc,
                        "chair": new_chair,
                        "meeting_type": new_type,
                        "notice_text": new_notice,
                        "status": "upcoming"
                    }).execute()
                    st.success("Meeting scheduled!")
                    st.rerun()
                else:
                    st.warning("Please enter a chair name.")

    # List meetings
    meetings = db_meetings()
    if not meetings:
        st.markdown('<div class="info-box">📋 No meetings have been scheduled yet.</div>', unsafe_allow_html=True)
    else:
        status_colors = {"upcoming": "badge-upcoming", "open": "badge-open", "draft": "badge-draft", "finalised": "badge-finalised"}
        status_labels = {"upcoming": "Upcoming", "open": "Open", "draft": "Draft Minutes", "finalised": "Finalised"}

        for m in meetings:
            badge = status_colors.get(m.get("status","upcoming"), "badge-upcoming")
            label = status_labels.get(m.get("status","upcoming"), m.get("status","").title())
            card_class = m.get("status","upcoming")

            with st.container():
                st.markdown(f"""
                <div class="meeting-card {card_class}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <h3>📋 {m.get('meeting_type','Ordinary')} Meeting — {fmt_date(m.get('meeting_date'))}</h3>
                    <span class="status-badge {badge}">{label}</span>
                  </div>
                  <div class="meta">
                    <span>⏰ {m.get('start_time','')[:5] if m.get('start_time') else '—'}</span>
                    <span>📍 {m.get('location','—')}</span>
                    <span>👤 Chair: {m.get('chair','—')}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Open Meeting →", key=f"open_{m['id']}", use_container_width=False):
                    st.session_state.selected_meeting = m['id']
                    st.session_state.view = "meeting"

    # ── MEETING DETAIL VIEW ──────────────────────────────────────────────────────
    if st.session_state.get("view") == "meeting" and st.session_state.get("selected_meeting"):
        mid = st.session_state.selected_meeting
        m = db_meeting(mid)
        if not m:
            st.error("Meeting not found.")
        else:
            st.markdown("---")
            # Back button
            if st.button("← Back to all meetings"):
                st.session_state.view = None
                st.session_state.selected_meeting = None
                st.rerun()

            status = m.get("status", "upcoming")
            badge = status_colors.get(status, "badge-upcoming")
            label = status_labels.get(status, status.title())

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a2e4a,#2d4a6e);color:white;padding:1.5rem;border-radius:10px;margin-bottom:1rem;">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <h2 style="margin:0;font-size:1.4rem;">{m.get('meeting_type','Ordinary')} Meeting</h2>
                  <p style="margin:0.25rem 0 0;opacity:0.8;">{fmt_date(m.get('meeting_date'))} &nbsp;·&nbsp; {m.get('start_time','')[:5] if m.get('start_time') else ''} &nbsp;·&nbsp; {m.get('location','')}</p>
                  <p style="margin:0.25rem 0 0;opacity:0.7;font-size:0.85rem;">Chair: {m.get('chair','—')}</p>
                </div>
                <span class="status-badge {badge}" style="font-size:0.85rem;">{label}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Admin status update
            if check_admin():
                col_s1, col_s2, col_s3 = st.columns([2,1,1])
                with col_s1:
                    new_status = st.selectbox("Update status", ["upcoming","open","draft","finalised"],
                        index=["upcoming","open","draft","finalised"].index(status) if status in ["upcoming","open","draft","finalised"] else 0,
                        key=f"status_{mid}")
                with col_s2:
                    st.write("")
                    st.write("")
                    if st.button("Update Status", key=f"upd_status_{mid}"):
                        supabase.table("pac_meetings").update({"status": new_status}).eq("id", mid).execute()
                        st.success("Status updated.")
                        st.rerun()
                with col_s3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Delete Meeting", key=f"del_{mid}", type="secondary"):
                        st.session_state[f"confirm_del_{mid}"] = True

                if st.session_state.get(f"confirm_del_{mid}"):
                    st.warning("⚠️ Are you sure? This will delete the meeting and all related data.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, delete", key=f"yes_del_{mid}", type="primary"):
                            for t in ["pac_agenda_items","pac_attendance","pac_minutes","pac_action_items","pac_documents"]:
                                supabase.table(t).delete().eq("meeting_id", mid).execute()
                            supabase.table("pac_meetings").delete().eq("id", mid).execute()
                            st.session_state.view = None
                            st.session_state.selected_meeting = None
                            st.rerun()
                    with c2:
                        if st.button("Cancel", key=f"no_del_{mid}"):
                            st.session_state[f"confirm_del_{mid}"] = False
                            st.rerun()

            # ── TABS WITHIN MEETING ──────────────────────────────────────────────
            mt1, mt2, mt3, mt4, mt5 = st.tabs(["📋 Agenda", "👥 Attendance", "📝 Minutes", "✅ Actions", "📎 Documents"])

            # ── AGENDA TAB ───────────────────────────────────────────────────────
            with mt1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### 📋 Agenda Items")

                if m.get("notice_text"):
                    st.markdown(f'<div class="info-box">ℹ️ {m["notice_text"]}</div>', unsafe_allow_html=True)

                # Standard DfE PAC agenda structure
                st.markdown("""
                **Standard Agenda Order (DfE PAC Requirements):**
                1. Welcome & Acknowledgement of Country
                2. Apologies
                3. Confirmation of previous minutes
                4. Business arising from previous minutes
                5. Correspondence
                6. General business *(submitted items appear here)*
                7. Any other business
                8. Date of next meeting
                """)
                st.markdown("---")

                items = db_agenda(mid)
                if items:
                    st.markdown("**Submitted Agenda Items for General Business:**")
                    for i, item in enumerate(items):
                        item_type_icon = {"Information": "ℹ️", "Discussion": "💬", "Decision": "⚖️", "Presentation": "📊"}.get(item.get("item_type",""), "📌")
                        st.markdown(f"""
                        <div class="agenda-item">
                          <h4>{item_type_icon} {item.get('item_title','Untitled')}</h4>
                          <p>{item.get('item_description','')}</p>
                          <div class="submitter">Submitted by: {item.get('submitted_by','—')} &nbsp;·&nbsp; Type: {item.get('item_type','General')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if check_admin():
                            if st.button("🗑️", key=f"del_ai_{item['id']}", help="Remove this agenda item"):
                                supabase.table("pac_agenda_items").delete().eq("id", item["id"]).execute()
                                st.rerun()
                else:
                    st.markdown('<div class="info-box">No agenda items submitted yet.</div>', unsafe_allow_html=True)

                # Submit agenda item (all staff)
                if status in ["upcoming", "open"]:
                    st.markdown("---")
                    st.markdown("**➕ Submit an Agenda Item**")
                    st.markdown('<div class="info-box">All staff can submit items for general business consideration.</div>', unsafe_allow_html=True)
                    with st.form(f"agenda_form_{mid}", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            ai_name = st.text_input("Your name *", key=f"ai_name_{mid}")
                            ai_title = st.text_input("Agenda item title *", key=f"ai_title_{mid}")
                        with col2:
                            ai_type = st.selectbox("Item type", ["Information","Discussion","Decision","Presentation"], key=f"ai_type_{mid}")
                        ai_desc = st.text_area("Description / background (optional)", key=f"ai_desc_{mid}")
                        if st.form_submit_button("Submit Agenda Item", type="primary", use_container_width=True):
                            if ai_name.strip() and ai_title.strip():
                                existing = db_agenda(mid)
                                order = len(existing) + 1
                                supabase.table("pac_agenda_items").insert({
                                    "meeting_id": mid,
                                    "submitted_by": ai_name.strip(),
                                    "item_title": ai_title.strip(),
                                    "item_description": ai_desc.strip(),
                                    "item_type": ai_type,
                                    "order_no": order
                                }).execute()
                                st.success("✅ Agenda item submitted successfully!")
                                st.rerun()
                            else:
                                st.warning("Please enter your name and item title.")
                elif status == "finalised":
                    st.markdown('<div class="warn-box">⚠️ This meeting has been finalised. Agenda items can no longer be submitted.</div>', unsafe_allow_html=True)

                # Export agenda (admin)
                if check_admin() and items:
                    st.markdown("---")
                    agenda_text = f"""PERSONNEL ADVISORY COMMITTEE
Cowandilla Learning Centre

MEETING AGENDA — {m.get('meeting_type','Ordinary').upper()} MEETING
Date: {fmt_date(m.get('meeting_date'))}
Time: {m.get('start_time','')[:5] if m.get('start_time') else '—'}
Location: {m.get('location','—')}
Chair: {m.get('chair','—')}

════════════════════════════════════════════

AGENDA

1. Welcome & Acknowledgement of Country
2. Apologies
3. Confirmation of previous minutes
4. Business arising from previous minutes
5. Correspondence
6. General Business

"""
                    for i, item in enumerate(items):
                        agenda_text += f"   6.{i+1}  [{item.get('item_type','')}] {item.get('item_title','')}\n"
                        if item.get("item_description"):
                            agenda_text += f"         {item.get('item_description','')}\n"
                        agenda_text += f"         Submitted by: {item.get('submitted_by','')}\n\n"
                    agenda_text += """7. Any Other Business
8. Date of Next Meeting

════════════════════════════════════════════
This agenda has been prepared in accordance with DfE PAC requirements.
"""
                    st.download_button("📄 Download Agenda (TXT)", agenda_text,
                        file_name=f"PAC_Agenda_{m.get('meeting_date','')}.txt",
                        mime="text/plain", use_container_width=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # ── ATTENDANCE TAB ───────────────────────────────────────────────────
            with mt2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### 👥 Attendance Register")

                attendance = db_attendance(mid)

                # Admin: add staff to register
                if check_admin():
                    with st.expander("➕ Add Staff Member to Register"):
                        with st.form(f"att_form_{mid}", clear_on_submit=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                att_name = st.text_input("Staff name *")
                                att_role = st.text_input("Role / position")
                            with col2:
                                att_status = st.selectbox("Status", ["Present","Apology","Absent"])
                            if st.form_submit_button("Add to Register", type="primary"):
                                if att_name.strip():
                                    supabase.table("pac_attendance").insert({
                                        "meeting_id": mid,
                                        "staff_name": att_name.strip(),
                                        "role": att_role.strip(),
                                        "attended": att_status == "Present",
                                        "apology": att_status == "Apology"
                                    }).execute()
                                    st.rerun()
                                else:
                                    st.warning("Please enter a staff name.")

                if attendance:
                    present = [a for a in attendance if a.get("attended")]
                    apologies = [a for a in attendance if a.get("apology")]
                    absent = [a for a in attendance if not a.get("attended") and not a.get("apology")]

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Present", len(present))
                    col2.metric("Apologies", len(apologies))
                    col3.metric("Absent", len(absent))

                    st.markdown("---")

                    if present:
                        st.markdown("**✅ Present**")
                        for a in present:
                            c1, c2 = st.columns([4,1])
                            with c1:
                                st.markdown(f"👤 **{a['staff_name']}** — {a.get('role','')}")
                            with c2:
                                if check_admin():
                                    if st.button("✕", key=f"del_att_{a['id']}"):
                                        supabase.table("pac_attendance").delete().eq("id", a["id"]).execute()
                                        st.rerun()

                    if apologies:
                        st.markdown("**📨 Apologies**")
                        for a in apologies:
                            c1, c2 = st.columns([4,1])
                            with c1:
                                st.markdown(f"👤 **{a['staff_name']}** — {a.get('role','')}")
                            with c2:
                                if check_admin():
                                    if st.button("✕", key=f"del_att_{a['id']}"):
                                        supabase.table("pac_attendance").delete().eq("id", a["id"]).execute()
                                        st.rerun()

                    if absent:
                        st.markdown("**❌ Absent (no apology)**")
                        for a in absent:
                            c1, c2 = st.columns([4,1])
                            with c1:
                                st.markdown(f"👤 **{a['staff_name']}** — {a.get('role','')}")
                            with c2:
                                if check_admin():
                                    if st.button("✕", key=f"del_att_{a['id']}"):
                                        supabase.table("pac_attendance").delete().eq("id", a["id"]).execute()
                                        st.rerun()
                else:
                    st.markdown('<div class="info-box">No attendance has been recorded yet.</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # ── MINUTES TAB ─────────────────────────────────────────────────────
            with mt3:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### 📝 Meeting Minutes")

                mins = db_minutes(mid)

                if check_admin():
                    st.markdown("**Admin: Record/Edit Minutes**")
                    if mins:
                        mins_content = mins.get("content","")
                        mins_status = mins.get("status","draft")
                    else:
                        # Generate a template
                        items = db_agenda(mid)
                        attendance = db_attendance(mid)
                        present_names = ", ".join([a["staff_name"] for a in attendance if a.get("attended")]) or "—"
                        apology_names = ", ".join([a["staff_name"] for a in attendance if a.get("apology")]) or "Nil"
                        agenda_items_text = ""
                        for i, item in enumerate(items):
                            agenda_items_text += f"\n6.{i+1} {item.get('item_title','')}\n     Discussion: \n     Outcome: \n"

                        mins_content = f"""PERSONNEL ADVISORY COMMITTEE
Cowandilla Learning Centre
{m.get('meeting_type','Ordinary').upper()} MEETING MINUTES

Date: {fmt_date(m.get('meeting_date'))}
Time: {m.get('start_time','')[:5] if m.get('start_time') else '—'}
Location: {m.get('location','—')}
Chair: {m.get('chair','—')}

════════════════════════════════════════════

1. WELCOME & ACKNOWLEDGEMENT OF COUNTRY
   The Chair opened the meeting at [TIME] and acknowledged the Kaurna people as the traditional custodians of the land on which we meet.

2. APOLOGIES
   Apologies received from: {apology_names}
   Present: {present_names}

3. CONFIRMATION OF PREVIOUS MINUTES
   

4. BUSINESS ARISING FROM PREVIOUS MINUTES
   

5. CORRESPONDENCE
   Inwards: 
   Outwards: 

6. GENERAL BUSINESS
{agenda_items_text}

7. ANY OTHER BUSINESS
   

8. DATE OF NEXT MEETING
   The next meeting will be held on: 

════════════════════════════════════════════
Meeting closed at: [TIME]
Minutes prepared by: 
Date prepared: {date.today().strftime('%-d %B %Y')}
"""
                        mins_status = "draft"

                    mins_edit = st.text_area("Minutes content", value=mins_content, height=500, key=f"mins_edit_{mid}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Save Draft", key=f"save_draft_{mid}", use_container_width=True):
                            if mins:
                                supabase.table("pac_minutes").update({"content": mins_edit, "status": "draft"}).eq("id", mins["id"]).execute()
                            else:
                                supabase.table("pac_minutes").insert({"meeting_id": mid, "content": mins_edit, "status": "draft"}).execute()
                            st.success("Draft saved.")
                            st.rerun()
                    with col2:
                        if st.button("✅ Finalise Minutes", key=f"finalise_{mid}", use_container_width=True, type="primary"):
                            if mins:
                                supabase.table("pac_minutes").update({
                                    "content": mins_edit, "status": "finalised",
                                    "finalised_at": datetime.now().isoformat()
                                }).eq("id", mins["id"]).execute()
                            else:
                                supabase.table("pac_minutes").insert({
                                    "meeting_id": mid, "content": mins_edit,
                                    "status": "finalised", "finalised_at": datetime.now().isoformat()
                                }).execute()
                            supabase.table("pac_meetings").update({"status": "finalised"}).eq("id", mid).execute()
                            st.success("✅ Minutes finalised and meeting status updated.")
                            st.rerun()
                    with col3:
                        if mins and mins_edit:
                            st.download_button("📄 Export", mins_edit,
                                file_name=f"PAC_Minutes_{m.get('meeting_date','')}.txt",
                                mime="text/plain", use_container_width=True)

                else:
                    # Staff view
                    if mins:
                        if mins.get("status") == "finalised":
                            st.markdown('<div class="info-box">✅ These minutes have been finalised.</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="warn-box">⏳ Minutes are in draft — not yet finalised by admin.</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="minutes-box">{mins.get("content","")}</div>', unsafe_allow_html=True)
                        st.download_button("📄 Download Minutes", mins.get("content",""),
                            file_name=f"PAC_Minutes_{m.get('meeting_date','')}.txt",
                            mime="text/plain")
                    else:
                        st.markdown('<div class="info-box">📝 Minutes have not been recorded yet. Check back after the meeting.</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # ── ACTIONS TAB ─────────────────────────────────────────────────────
            with mt4:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### ✅ Action Items")

                actions = db_actions(mid)

                # Admin: add action
                if check_admin():
                    with st.expander("➕ Add Action Item"):
                        with st.form(f"action_form_{mid}", clear_on_submit=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                act_text = st.text_area("Action *")
                                act_person = st.text_input("Responsible person *")
                            with col2:
                                act_due = st.date_input("Due date", value=date.today() + timedelta(weeks=4))
                                act_status = st.selectbox("Status", ["Pending","In Progress","Complete"])
                            if st.form_submit_button("Add Action", type="primary"):
                                if act_text.strip() and act_person.strip():
                                    supabase.table("pac_action_items").insert({
                                        "meeting_id": mid,
                                        "action": act_text.strip(),
                                        "responsible_person": act_person.strip(),
                                        "due_date": str(act_due),
                                        "status": act_status
                                    }).execute()
                                    st.rerun()

                if actions:
                    pending = [a for a in actions if a.get("status") != "Complete"]
                    done = [a for a in actions if a.get("status") == "Complete"]

                    if pending:
                        st.markdown(f"**Pending / In Progress ({len(pending)})**")
                        for a in pending:
                            status_icon = "🔄" if a.get("status") == "In Progress" else "⏳"
                            overdue = ""
                            if a.get("due_date"):
                                try:
                                    due = datetime.strptime(str(a["due_date"])[:10], "%Y-%m-%d").date()
                                    if due < date.today():
                                        overdue = " 🔴 **OVERDUE**"
                                except:
                                    pass
                            st.markdown(f"""
                            <div class="action-item">
                              <strong>{status_icon} {a.get('action','')}</strong>{overdue}
                              <br><small>👤 {a.get('responsible_person','—')} &nbsp;·&nbsp; 📅 Due: {fmt_date(a.get('due_date'))}</small>
                            </div>
                            """, unsafe_allow_html=True)

                            if check_admin():
                                c1, c2, c3 = st.columns([2,2,1])
                                with c1:
                                    new_st = st.selectbox("Status", ["Pending","In Progress","Complete"],
                                        index=["Pending","In Progress","Complete"].index(a.get("status","Pending")),
                                        key=f"act_st_{a['id']}")
                                with c2:
                                    st.write("")
                                    st.write("")
                                    if st.button("Update", key=f"upd_act_{a['id']}"):
                                        supabase.table("pac_action_items").update({"status": new_st}).eq("id", a["id"]).execute()
                                        st.rerun()
                                with c3:
                                    st.write("")
                                    st.write("")
                                    if st.button("🗑️", key=f"del_act_{a['id']}"):
                                        supabase.table("pac_action_items").delete().eq("id", a["id"]).execute()
                                        st.rerun()

                    if done:
                        st.markdown(f"**Completed ({len(done)})**")
                        for a in done:
                            st.markdown(f"""
                            <div class="action-item action-done">
                              <strong>✅ {a.get('action','')}</strong>
                              <br><small>👤 {a.get('responsible_person','—')} &nbsp;·&nbsp; 📅 Due: {fmt_date(a.get('due_date'))}</small>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="info-box">No action items recorded yet.</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # ── DOCUMENTS TAB ────────────────────────────────────────────────────
            with mt5:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### 📎 Supporting Documents")

                docs = db_docs(mid)

                if check_admin():
                    with st.expander("➕ Add Document Link"):
                        with st.form(f"doc_form_{mid}", clear_on_submit=True):
                            doc_name = st.text_input("Document name *")
                            doc_url = st.text_input("URL / link *")
                            doc_desc = st.text_input("Description (optional)")
                            if st.form_submit_button("Add Document", type="primary"):
                                if doc_name.strip() and doc_url.strip():
                                    supabase.table("pac_documents").insert({
                                        "meeting_id": mid,
                                        "document_name": doc_name.strip(),
                                        "document_url": doc_url.strip(),
                                        "description": doc_desc.strip()
                                    }).execute()
                                    st.rerun()

                if docs:
                    for d in docs:
                        c1, c2 = st.columns([5,1])
                        with c1:
                            st.markdown(f"📄 **[{d.get('document_name','')}]({d.get('document_url','#')})** — {d.get('description','')}")
                        with c2:
                            if check_admin():
                                if st.button("🗑️", key=f"del_doc_{d['id']}"):
                                    supabase.table("pac_documents").delete().eq("id", d["id"]).execute()
                                    st.rerun()
                else:
                    st.markdown('<div class="info-box">No documents attached to this meeting.</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 – UPCOMING
# ════════════════════════════════════════════════════════════════════════════════
with tab_upcoming:
    meetings = db_meetings()
    upcoming = [m for m in meetings if m.get("status") in ["upcoming","open"]]

    if not upcoming:
        st.markdown('<div class="info-box">No upcoming meetings scheduled.</div>', unsafe_allow_html=True)
    else:
        for m in upcoming:
            meeting_date = datetime.strptime(str(m.get("meeting_date",""))[:10], "%Y-%m-%d").date() if m.get("meeting_date") else None
            days_until = (meeting_date - date.today()).days if meeting_date else None
            days_text = f"({days_until} days away)" if days_until is not None and days_until >= 0 else ("(today!)" if days_until == 0 else "")

            st.markdown(f"""
            <div class="meeting-card upcoming">
              <h3>📋 {m.get('meeting_type','Ordinary')} Meeting — {fmt_date(m.get('meeting_date'))} {days_text}</h3>
              <div class="meta">
                <span>⏰ {m.get('start_time','')[:5] if m.get('start_time') else '—'}</span>
                <span>📍 {m.get('location','—')}</span>
                <span>👤 Chair: {m.get('chair','—')}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            items = db_agenda(m["id"])
            if items:
                st.markdown(f"**Agenda items submitted ({len(items)}):**")
                for item in items:
                    st.markdown(f"  - {item.get('item_title','')} *(submitted by {item.get('submitted_by','')})*")

            st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 – ACTION REGISTER (across all meetings)
# ════════════════════════════════════════════════════════════════════════════════
with tab_actions:
    st.markdown("### ✅ Full Action Register — All Meetings")
    st.markdown("All outstanding and recent action items across all PAC meetings.")

    meetings = db_meetings()
    all_actions = []
    for m in meetings:
        actions = db_actions(m["id"])
        for a in actions:
            a["_meeting_date"] = m.get("meeting_date","")
            a["_meeting_type"] = m.get("meeting_type","")
            all_actions.append(a)

    pending = [a for a in all_actions if a.get("status") != "Complete"]
    completed = [a for a in all_actions if a.get("status") == "Complete"]

    if not all_actions:
        st.markdown('<div class="info-box">No action items recorded across any meetings yet.</div>', unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Actions", len(all_actions))
        col2.metric("Pending / In Progress", len(pending))
        col3.metric("Complete", len(completed))

        st.markdown("---")
        if pending:
            st.markdown("#### Pending / In Progress")
            for a in sorted(pending, key=lambda x: x.get("due_date","") or ""):
                overdue = ""
                if a.get("due_date"):
                    try:
                        due = datetime.strptime(str(a["due_date"])[:10], "%Y-%m-%d").date()
                        if due < date.today():
                            overdue = " 🔴 OVERDUE"
                    except:
                        pass
                status_icon = "🔄" if a.get("status") == "In Progress" else "⏳"
                st.markdown(f"""
                <div class="action-item">
                  <strong>{status_icon} {a.get('action','')}</strong>{overdue}
                  <br><small>👤 {a.get('responsible_person','—')} &nbsp;·&nbsp; 📅 Due: {fmt_date(a.get('due_date'))} &nbsp;·&nbsp; Meeting: {a.get('_meeting_type','')} {fmt_date(a.get('_meeting_date'))}</small>
                </div>
                """, unsafe_allow_html=True)

                if check_admin():
                    c1, c2 = st.columns([3,1])
                    with c1:
                        new_st = st.selectbox("Update", ["Pending","In Progress","Complete"],
                            index=["Pending","In Progress","Complete"].index(a.get("status","Pending")),
                            key=f"reg_st_{a['id']}")
                    with c2:
                        st.write("")
                        st.write("")
                        if st.button("Save", key=f"reg_upd_{a['id']}"):
                            supabase.table("pac_action_items").update({"status": new_st}).eq("id", a["id"]).execute()
                            st.rerun()

        if completed:
            with st.expander(f"View completed actions ({len(completed)})"):
                for a in completed:
                    st.markdown(f"""
                    <div class="action-item action-done">
                      <strong>✅ {a.get('action','')}</strong>
                      <br><small>👤 {a.get('responsible_person','—')} &nbsp;·&nbsp; Meeting: {a.get('_meeting_type','')} {fmt_date(a.get('_meeting_date'))}</small>
                    </div>
                    """, unsafe_allow_html=True)

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;color:#999;font-size:0.8rem;">
  Cowandilla Learning Centre · Personnel Advisory Committee · 
  Built in accordance with DfE workplace consultation requirements
</div>
""", unsafe_allow_html=True)
