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
    df = pd.read_csv("survey_questions_grouped.csv")
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

# Save Responses Function
def save_responses():
    try:
        end_time = datetime.datetime.now()
        duration = end_time - st.session_state["start_time"]
        respondent_id = st.session_state["respondent_id"]
        timestamp = end_time.strftime("%Y-%m-%d_%H-%M-%S")
        career = st.session_state["career"].strip().replace(" ", "_")

        # Create output directory if it doesn't exist
        output_folder = "./survey_responses"
        os.makedirs(output_folder, exist_ok=True)
        filename = f"{career}_{respondent_id}_{timestamp}.csv"
        full_path = os.path.join(output_folder, filename)

        # Compile all responses including profession
        records = [{
            "RespondentID": respondent_id,
            "Timestamp": timestamp,
            "Career": st.session_state["career"],
            "IdentificationCode": st.session_state.get("identification_code", ""),
            "DurationSeconds": int(duration.total_seconds()),
            "Group": "Participant Info",
            "Question": "Profession",
            "Answer": st.session_state["career"],
            "NumericValue": None,
            "Direction": None
        }]
        
        # Add all survey responses
        for group in groups:
            group_df = df[df["Group"] == group]
            for idx, row in group_df.iterrows():
                q_key = f"{group}_{idx}"
                value = st.session_state["responses"].get(q_key, 1)
                
                records.append({
                    "RespondentID": respondent_id,
                    "Timestamp": timestamp,
                    "Career": st.session_state["career"],
                    "DurationSeconds": int(duration.total_seconds()),
                    "Group": group,
                    "Question": row["Question"],
                    "Answer": f"Option A {abs(value)}x" if value > 1 else 
                             f"Option B {abs(value)}x" if value < -1 else 
                             "Equal (1)",
                    "NumericValue": value,
                    "Direction": "A" if value > 1 else "B" if value < -1 else "Equal"
                })

        # Create DataFrame and save
        result_df = pd.DataFrame(records)
        result_df.to_csv(full_path, index=False)
        
        # Send email with attachment
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
    st.title("Expert Survey: The Importance of Design Principles on Electronic Instrument System")
    st.markdown("""
    Dear respondents,

    My name is Dhifan, and I am a Master's student at the Technical University of Munich (TUM), currently conducting my thesis at TADYX6 – Airbus Defence and Space. 
    
    As part of this research, I hope to gather expert insights from professionals like you to determine the relative importance—or weight—of various design principles used in Electronic Instrument System (EIS) evaluation. These weights will help prioritize design rules, especially in complex or abstract systems where user perspectives may differ.  
    
    Your input will inform the development of a scoring system grounded in real-world relevance. The collected data will support the creation of automatic evaluation tools for EIS design—enabling more consistent, user-centered, and efficient assessments.

    Thank you for your time and expertise.
    """)

    st.subheader("Guidance")
    st.markdown("At the beginning of the survey, you will find brief explanations of EIS, key design principles, and interface heuristics. These summaries are intended to provide context and support your understanding as you respond to the survey questions. You are welcome to revisit these explanations at any point during the survey by scrolling up, especially if you need a quick refresher or clarification while answering. Please take your time, and answer based on your professional judgment and expectations.")

    st.subheader("Electronic Instrument System")
    st.image("efis.jpg", use_container_width=True, caption="Electronic Flight Instrument System")
    st.markdown("""
    An Electronic Instrument System (EIS) is a flight instrument display system in an aircraft cockpit that displays flight data electronically. It consists of Electronic Flight Instrument System (EFIS) and Electronic Centralized Aircraft Monitoring (ECAM) and acts as the primary visual interfaces that present critical flight information to pilots. These systems integrate data from sensors, navigation systems, engine systems, and aircraft controls into a consolidated, user-friendly format. Modern displays often use glass cockpit technology (digital screens), replacing traditional electromechanical display to enhance situational awareness and reduce workload.

    Key Functions:
    - Primary Flight Displays (PFDs): Show altitude, airspeed, attitude, and heading.
    - Navigation Displays (NDs): Provide route maps, waypoints, and traffic/terrain alerts.
    - Engine Indicating and Crew Alerting System (EICAS): Monitor aircraft health and alert pilots to anomalies.
    - Multifunction Displays (MFDs): Allow interaction with subsystems (fuel, weather).

    Design Goals:
    - Clarity: Information must be unambiguous and quickly interpretable.
    - Prioritization: Critical data (warnings) should stand out.
    - Consistency: Follow standardized conventions to reduce cognitive load.
    - Ergonomics: Ensure readability under varying lighting/operational conditions.

    Image Reference: https://karlenepetitt.blogspot.com/2012/01/a330-terminology-its-all-foreign.html
    """)
    
    # --- Insert images and group intros ---
    st.subheader("**Gestalt Laws**")
    st.image("gestalt.png", use_container_width=True, caption="Gestalt Principles Overview")
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

    st.subheader("**Wickens' 13 Principles of Display Design**")
    st.image("wickens.png", use_container_width=True, caption="Wickens' Principles Overview")
    st.markdown("""
    - **Make Display Legible**: Ensure text, symbols, and graphics are easy to read.  
    - **Avoid Absolute Judgement Limits**: Avoid overreliance on subtle sensory cues (like color only).  
    - **Top-Down Processing**: Design should align with user expectations.  
    - **Redundancy Gain**: Present information in more than one way.  
    - **Discriminability**: Make differences between items noticeable.  
    - **Principle of Pictorial Realism**: Represent information in ways that mimic real-world structure.  
    - **Principle of the Moving Part**: Display motion should reflect actual or expected direction.  
    - **Minimize Access Costs**: Frequently needed info should be easy to find.  
    - **Proximity Compatibility Principle**: Related items should be close together.  
    - **Principle of Multiple Resources**: Distribute information across visual, auditory, spatial channels.  
    - **Principle of Predictive Aiding**: Help users anticipate what's coming.  
    - **Replace Memory with Visual Information**: Keep important data visible.  
    - **Principle of Consistency**: Use familiar and repeated conventions.  
    """)

    st.subheader("**Ergonomics/Interface Design Heuristics**")
    st.image("ergonomics.png", use_container_width=True, caption="Ergonomic and Interface Heuristics")
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

    st.subheader("**How to Answer the Questions**")
    st.image("intensity_scale.png", use_container_width=True, caption="Pairwise Comparison Scale")
    st.markdown("""
    For each question, you'll be comparing two design principles (Option A vs Option B) using the following scale:
    
    - **9**: Option A is extremely more important than Option B  
    - **7**: Option A is very strongly more important than Option B  
    - **5**: Option A is strongly more important than Option B  
    - **3**: Option A is moderately more important than Option B  
    - **1**: Both options are equally important  
    - **3**: Option B is moderately more important than Option A  
    - **5**: Option B is strongly more important than Option A  
    - **7**: Option B is very strongly more important than Option A  
    - **9**: Option B is extremely more important than Option A  
    
    Use intermediate values (2,4,6,8) when you need to make finer distinctions between these levels.
    """)

    st.markdown("""
    **References**
    - Wasson, James W. (2019), Electronic Instrument Systems.
    - Wagemans, J., et. al. (2012), A Century of Gestalt Psychology in Visual Perception I.
    - Wickens, Christopher D., et. al., (1997), An Introduction to Human Factors Engineering. 
    """)

    st.divider()

    # Identification question 
    st.markdown("""
    **Identification for Data Management**
    
    By submitting your answer, you acknowledge that your data will be used for research purposes. You also confirm that you are aware of and agree to the data protection document attached to the email containing this questionnaire. 
    
    Since the questionnaire is anonymous, you are required to answer the following question so that in the future, 
    if you wish to destroy the data, you can identify your set of data and inform which to destroy. 
    
    Please type in capital letters and in continuous format:
    - First two letters of mother's first name
    - First two letters of father's first name
    - Month of mother's birth month (two digits)
    - Month of father's birth month (two digits)
    
    Example: Heike, Franz, March, May → HEFR0305
    """)
    
    identification_code = st.text_input(
        "**Enter your identification code:**",
        key="identification_code",
        max_chars=8,
        help="Format: First 2 letters of mother's name + first 2 letters of father's name + mother's birth month (2 digits) + father's birth month (2 digits)"
    )
    
    # Validate format if provided
    if identification_code and len(identification_code) == 8:
        try:
            # Check if last 4 characters are digits representing months (01-12)
            month_part = identification_code[4:]
            if not (month_part.isdigit() and 1 <= int(month_part[:2]) <= 12 and 1 <= int(month_part[2:]) <= 12):
                st.warning("Please ensure the month parts are valid (01-12 for each). Example: HEFR0305")
        except:
            st.warning("Please check the format. Example: HEFR0305")

    # Career
    st.session_state["career"] = st.selectbox(
        "**What is your current profession or field of work?**",
        ["Pilot", "Operators", "Aerospace Engineer", "UI/UX Designer", 
         "Human Factors Engineers", "Researcher", "Student", "Other"],
        key="career_select"
    )
    
    if st.session_state["career"] == "Other":
        st.session_state["career"] = st.text_input("Please specify your profession", key="career_other")

    # --- Question Loop ---
    slider_values = [9, 8, 7, 6, 5, 4, 3, 2, 1, -2, -3, -4, -5, -6, -7, -8, -9]
    slider_labels = ["9", "8", "7", "6", "5", "4", "3", "2", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    for group in groups:
        group_df = df[df["Group"] == group]
        with st.expander(group):
            for idx, row in group_df.iterrows():
                q_key = f"{group}_{idx}"
                
                # Initialize response if not exists
                if q_key not in st.session_state["responses"]:
                    st.session_state["responses"][q_key] = 1  # Default neutral value
                
                # Display question
                st.write(f"{idx + 1}. {row['Question']}")
                
                # Create the slider with a unique key
                answer = st.select_slider(
                    "Importance:",
                    options=slider_values,
                    value=st.session_state["responses"][q_key],
                    format_func=lambda x: slider_labels[slider_values.index(x)],
                    key=f"slider_{q_key}"
                )
                
                # Store the response immediately
                st.session_state["responses"][q_key] = answer

    # --- Submission Section ---
    if st.button("Submit Survey"):
        # Validate profession is selected
        if not st.session_state.get("career") or st.session_state["career"].strip() == "":
            st.error("Please select or specify your profession before submitting.")
        else:
            # Confirmation dialog
            if st.checkbox("I confirm that I have answered all questions to the best of my ability"):
                success, result = save_responses()
                if success:
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.error(f"Failed to save your responses. Error: {result}")
            else:
                st.warning("Please confirm that you've answered all questions before submitting.")

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


