import streamlit as st
import pandas as pd
import datetime
import uuid
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# --- Setup ---
st.set_page_config(page_title="Expert Survey", layout="centered")

# Initialize session state
if "start_time" not in st.session_state:
    st.session_state["start_time"] = datetime.datetime.now()
if "respondent_id" not in st.session_state:
    st.session_state["respondent_id"] = str(uuid.uuid4())[:8]
if "responses" not in st.session_state:
    st.session_state["responses"] = {}
if "career" not in st.session_state:
    st.session_state["career"] = ""
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "show_unanswered" not in st.session_state:
    st.session_state["show_unanswered"] = False

# --- Load Questions ---
@st.cache_data
def load_questions():
    df = pd.read_csv("Survey_Questions_Grouped.csv")
    return df

df = load_questions()
groups = df["Group"].unique()
total_questions = df.shape[0]

# --- Email Function ---
def send_email_with_attachment(file_path):
    sender_email = "itsffworldno5@gmail.com"
    receiver_email = "dhifan.akbar@tum.de"  
    password = "vzcejhcgtwwcbhia"
    
    # Create email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = f"New Survey Response: {os.path.basename(file_path)}"
    
    # Email body
    body = f"A new response has been submitted. See attached: {os.path.basename(file_path)}"
    message.attach(MIMEText(body, "plain"))
    
    # Attach CSV
    with open(file_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="csv")
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
        message.attach(attach)
    
    # Send email via Gmail
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# --- MODIFIED: Save Responses Function ---
def save_responses():
    try:
        end_time = datetime.datetime.now()
        duration = end_time - st.session_state["start_time"]
        respondent_id = st.session_state["respondent_id"]
        timestamp = end_time.strftime("%Y-%m-%d_%H-%M-%S")
        career = st.session_state["career"].strip().replace(" ", "_")

        # Fixed output directory path
        output_folder = "./survey_responses"  # Changed to relative path for cloud compatibility
        os.makedirs(output_folder, exist_ok=True)
        filename = f"{career}_{respondent_id}_{timestamp}.csv"
        full_path = os.path.join(output_folder, filename)

        # Compile data
        records = [{
            "RespondentID": respondent_id,
            "Timestamp": timestamp,
            "Career": st.session_state["career"],
            "DurationSeconds": int(duration.total_seconds()),
            "Group": "Career",
            "Question": "Profession",
            "Answer": st.session_state["career"]
        }]
        
        for group in groups:
            questions = df[df["Group"] == group]["Question"].tolist()
            for idx, question in enumerate(questions):
                key = f"{group}_{df[df['Group'] == group].index[idx]}"
                records.append({
                    "RespondentID": respondent_id,
                    "Timestamp": timestamp,
                    "Career": st.session_state["career"],
                    "DurationSeconds": int(duration.total_seconds()),
                    "Group": group,
                    "Question": question,
                    "Answer": st.session_state["responses"].get(key, "")
                })

        result_df = pd.DataFrame(records)
        result_df.to_csv(full_path, index=False)
        
        # --- EMAIL SENDING NOW INSIDE TRY BLOCK ---
        email_sent = send_email_with_attachment(full_path)
        if not email_sent:
            st.warning("Responses saved locally, but email failed to send.")
        
        st.session_state["submitted"] = True
        return True, full_path
    except Exception as e:
        return False, str(e)

# --- Main Survey ---
if not st.session_state.get("submitted", False):
    # --- Introduction Section with Images ---
    st.title("Expert Survey on the Importance of Design Principles")
    st.markdown("""
    Dear respondents,

    My name is Dhifan, and I am a Master student from TUM. I am currently conducting my thesis at TADYX6 – Airbus Defence and Space.  
    
    As part of this research, I hope to gather expert insights from professionals like you to determine the relative importance—or weight—of various design principles used in display evaluation. These weights will help prioritize design rules, especially in complex or abstract systems where user perspectives may differ.  
    
    Your input will inform the development of a scoring system grounded in real-world relevance. The collected data will support the creation of automatic evaluation tools for aviation related interface display design for a more efficient assessments. Please keep the aviation context in mind when you are answering the questions.

    Thank you for your time and expertise.
    """)

    # --- Insert images and group intros ---
    st.subheader("Gestalt Laws (Perception-based)")
    st.image("Gestalt.png", use_container_width=True, caption="Gestalt Principles Overview")
    st.markdown("""
    - **Law of Closure**: We perceive incomplete shapes as complete figures by mentally "filling in" gaps.  
    - **Law of Continuity**: Elements arranged along a smooth path are perceived as part of a continuous pattern.  
    - **Law of Proximity**: Objects that are close together are seen as related or grouped.  
    - **Law of Experience**: We interpret visual information based on past knowledge or learned patterns.  
    - **Law of Prägnanz**: We tend to perceive the simplest, most stable and organized form possible.  
    - **Law of Similarity**: Items that look alike (shape, color, size) are perceived as part of the same group.  
    - **Law of Symmetry**: Symmetrical elements are naturally grouped and perceived as coherent, balanced figures.  
    - **Law of Common Fate**: Elements moving in the same direction are perceived as belonging together.  
    """)

    st.subheader("Wickens' 13 Principles of Display Design")
    st.image("Wickens.png", use_container_width=True, caption="Wickens' Principles Overview")
    st.markdown("""
    - **Make Display Legible**: Ensure text, symbols, and graphics are easy to read.  
    - **Avoid Absolute Judgement Limits**: Avoid overreliance on subtle sensory cues (like color only).  
    - **Top-Down Processing**: Design should align with user expectations.  
    - **Redundancy Gain**: Present information in more than one way.  
    - **Discriminability**: Make differences between items noticeable.  
    - **Pictorial Realism**: Represent information in ways that mimic real-world structure.  
    - **Moving Part**: Display motion should reflect actual or expected direction.  
    - **Minimize Access Costs**: Frequently needed info should be easy to find.  
    - **Proximity Compatibility**: Related items should be close together.  
    - **Multiple Resources**: Distribute information across visual, auditory, spatial channels.  
    - **Predictive Aiding**: Help users anticipate what's coming.  
    - **Replace Memory**: Keep important data visible.  
    - **Consistency**: Use familiar and repeated conventions.  
    """)

    st.subheader("Ergonomics / Interface Design Heuristics")
    st.image("Ergonomics.png", use_container_width=True, caption="Ergonomic and Interface Heuristics")
    st.markdown("""
    - **Frequency of Use**: Frequently used items should be easiest to reach.  
    - **Sequence of Use**: Place controls in the order they are typically used.  
    - **Importance**: Highlight critical information.  
    - **Visibility**: Important information must be easily seen.  
    - **Reachability**: Display should not require strain to view.  
    - **Consistency**: Keep formatting and structure uniform.  
    - **Stimulus-Response Compatibility**: Align control with user intuition.  
    - **Location Compatibility**: Place info where the user expects it.  
    """)

    # --- Career Input (Autosaved) ---
    st.session_state["career"] = st.text_input("What is your current profession or field of work?", st.session_state["career"])

    # --- Question Loop with Autosave and Progress Tracking ---
    unanswered_questions = []
    answered_count = 0
    
    for group in groups:
        group_df = df[df["Group"] == group]
        with st.expander(group):
            for idx, row in group_df.iterrows():
                q_key = f"{group}_{idx}"
                question_text = row["Question"]
                prev = st.session_state["responses"].get(q_key, "")
                
                # Highlight unanswered questions if submission was attempted
                is_unanswered = st.session_state["show_unanswered"] and q_key not in st.session_state["responses"]
                if is_unanswered:
                    unanswered_questions.append(f"{group} - Q{idx+1}: {question_text}")
                    st.markdown(f"<p style='color:red; font-weight:bold;'>❗ {idx + 1}. {question_text}</p>", unsafe_allow_html=True)
                else:
                    st.write(f"{idx + 1}. {question_text}")
                
                answer = st.radio("Select your answer:", ["", "Yes", "No"],
                                key=q_key, 
                                index=["", "Yes", "No"].index(prev) if prev else 0,
                                horizontal=True,
                                label_visibility="collapsed")
                
                if answer:
                    st.session_state["responses"][q_key] = answer

    # --- Progress Bar ---
    answered_count = sum(1 for v in st.session_state["responses"].values() if v != "")
    st.progress(answered_count / total_questions)

    # --- Submission Section ---
    if st.button("Submit Survey"):
        # Check for completeness
        unanswered = [k for k, v in st.session_state["responses"].items() if v == ""]
        if not st.session_state["career"].strip() or unanswered or len(st.session_state["responses"]) < total_questions:
            st.session_state["show_unanswered"] = True
            st.error("Please complete all questions before submitting:")
            
            # List all unanswered questions
            st.markdown("**Unanswered questions:**")
            for question in unanswered_questions:
                st.markdown(f"- {question}")
            
            st.warning("Please scroll up to answer the highlighted questions.")
        else:
            success, result = save_responses()
            if success:
                st.session_state["submitted"] = True
                st.rerun()
            else:
                st.error(f"Failed to save your responses. Error: {result}")
else:
    # --- Thank You Message ---
    st.title("Thank You!")
    st.success("Your responses have been saved successfully.")
    st.write("We appreciate your time and valuable input for this research.")
    st.balloons()
    
    if st.button("Start New Survey"):
        # Clear session state for a new survey
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
