
import re
import streamlit as st

from streamlit_ace import st_ace
from PyPDF2 import PdfReader

from resume_parsar import extract_resume_sections
from question_generater import generate_questions
from voice import audio_recording, transcribe_audio
from evaluation_agent import evaluate_answer


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

# Must be the first Streamlit command.
st.set_page_config(
    page_title="AI Mock Interviewer",
    page_icon="🎯",
    layout="centered"
)


# ==================================================
# 2. INITIALIZE SESSION STATE
# ==================================================

default_values = {
    "stage": "setup",
    "questions": [],
    "current_question": 0,
    "answers": {},
    "skills": [],
    "projects": [],
    "experience": [],
    "audio_key": 0,
    "temp_transcript": "",
    "evaluations": {},
    "scores": {}
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# 3. APPLICATION HEADER
# ==================================================

st.title("🎯 AI Mock Interviewer")

st.write(
    "Welcome to the AI Mock Interviewer! "
    "Upload your resume and prepare for your interview."
)


# ==================================================
# 4. SIDEBAR INPUTS
# ==================================================

st.sidebar.header("Student Credentials")

name = st.sidebar.text_input(
    "Please enter your name:"
)

role = st.sidebar.selectbox(
    "Please select the role you are interviewing for:",
    
    [
        "Python Developer",
        "Software Engineer",
        "Backend Developer",
        "Data Analyst",
        "Machine Learning Engineer",
        "Data Scientist",
        "Product Manager"
    ]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload your resume (PDF):",
    type=["pdf"]
)

process_resume = st.sidebar.button(
    "Process Resume"
)


# ==================================================
# 5. PROCESS RESUME
# ==================================================

if uploaded_file is not None:
    st.sidebar.success("Resume uploaded successfully!")

if process_resume:

    if not name.strip():
        st.sidebar.warning("Please enter your name.")

    elif uploaded_file is None:
        st.sidebar.warning("Please upload your resume.")

    else:

        try:
            # Read PDF
            uploaded_file.seek(0)

            reader = PdfReader(uploaded_file)

            resume_text = ""

            for page in reader.pages:
                text = page.extract_text()

                if text:
                    resume_text += text + "\n"

            if not resume_text.strip():
                st.sidebar.error(
                    "No readable text found in the PDF."
                )

            else:

                with st.spinner(
                    "Processing resume and generating questions..."
                ):

                    # Extract resume sections
                    skills, projects, experience = (
                        extract_resume_sections(resume_text)
                    )

                    # Generate interview questions
                    questions = generate_questions(
                        role,
                        skills,
                        projects,
                        experience
                    )

                # Normalize generated questions
                if isinstance(questions, str):
                    questions = [questions]

                questions = list(questions or [])

                if not questions:
                    st.sidebar.error(
                        "No interview questions were generated."
                    )

                else:

                    # Save extracted information
                    st.session_state.skills = skills
                    st.session_state.projects = projects
                    st.session_state.experience = experience

                    # Save generated questions
                    st.session_state.questions = questions

                    # Reset previous interview data
                    st.session_state.current_question = 0
                    st.session_state.answers = {}
                    st.session_state.evaluations = {}
                    st.session_state.scores = {}

                    st.session_state.temp_transcript = ""
                    st.session_state.audio_key += 1

                    # Move to summary stage
                    st.session_state.stage = "summary"

                    st.rerun()

        except Exception as e:
            st.sidebar.error(
                f"Resume processing failed: {e}"
            )


# ==================================================
# 6. SUMMARY STAGE
# ==================================================

if st.session_state.stage == "summary":

    st.divider()

    st.subheader("Candidate Summary")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("Skills")

        if st.session_state.skills:

            for skill in st.session_state.skills:
                st.write("•", skill)

        else:
            st.write("No skills detected.")

    with col2:

        st.subheader("Projects")

        if st.session_state.projects:

            for project in st.session_state.projects:
                st.write("•", project)

        else:
            st.write("No projects detected.")

    with col3:

        st.subheader("Experience")

        if st.session_state.experience:

            for exp in st.session_state.experience:
                st.write("•", exp)

        else:
            st.write("No experience detected.")

    st.divider()

    if st.button("Begin Interview"):

        if not st.session_state.questions:
            st.error("No questions available.")

        else:

            st.session_state.current_question = 0
            st.session_state.stage = "interview"

            st.rerun()


# ==================================================
# 7. INTERVIEW STAGE
# ==================================================

if st.session_state.stage == "interview":

    questions = st.session_state.questions

    total_questions = len(questions)

    if total_questions == 0:

        st.error("No questions available.")
        st.stop()

    # Validate question index
    current_question = st.session_state.current_question

    if current_question >= total_questions:
        current_question = total_questions - 1
        st.session_state.current_question = current_question

    question = questions[current_question]

    # Calculate progress
    progress = (current_question + 1) / total_questions

    st.progress(progress)

    st.subheader(
        f"Question {current_question + 1} of {total_questions}"
    )

    st.write(question)

    st.divider()

    # Retrieve previously saved answer
    answer = st.session_state.answers.get(
        current_question,
        ""
    )

    # --------------------------------------------------
    # 7A. CODING QUESTIONS
    # --------------------------------------------------

    if current_question < 2:

        st.write("Write your code below:")

        language = st.selectbox(
            "Select programming language:",
            ["Python", "JavaScript", "Java", "C++", "Go"],
            key=f"lang_{current_question}"
        )

        language_map = {
            "Python": "python",
            "JavaScript": "javascript",
            "Java": "java",
            "C++": "cpp",
            "Go": "golang"
        }

        selected_language = language_map[language]

        answer = st_ace(
            value=answer,
            language=selected_language,
            theme="monokai",
            height=320,
            auto_update=True,
            key=f"code_editor_{current_question}"
        )

        # Handle empty editor response
        if answer is None:
            answer = ""

    # --------------------------------------------------
    # 7B. VOICE QUESTIONS
    # --------------------------------------------------

    else:

        st.write("Record your answer below:")

        audio = audio_recording(
            key=(
                f"audio_{current_question}_"
                f"{st.session_state.audio_key}"
            )
        )

        # Transcribe only when the user clicks the button
        if st.button(
            "Transcribe Recording",
            key=f"transcribe_{current_question}"
        ):

            if audio is not None and len(audio) > 0:

                try:

                    with st.spinner("Transcribing audio..."):

                        text = transcribe_audio(audio)

                    if text:

                        st.session_state.temp_transcript = text

                        st.success("Transcription successful!")

                    else:
                        st.warning(
                            "No speech detected in the recording."
                        )

                except Exception as e:

                    st.error(
                        f"Transcription failed: {e}"
                    )

            else:
                st.warning("Please record your answer first.")

        # Display temporary transcript
        if st.session_state.temp_transcript:

            st.write("Latest Recording:")

            st.write(
                st.session_state.temp_transcript
            )

        # Save transcript as answer
        if st.button(
            "Save Recording as Answer",
            key=f"save_recording_{current_question}"
        ):

            if st.session_state.temp_transcript:

                st.session_state.answers[current_question] = (
                    st.session_state.temp_transcript
                )

                st.success(
                    "Recording saved as answer successfully!"
                )

            else:

                st.warning(
                    "Record and transcribe your answer first."
                )

        # Display previously saved answer
        if current_question in st.session_state.answers:

            st.divider()

            st.success("Saved Answer:")

            st.write(
                st.session_state.answers[current_question]
            )

    # --------------------------------------------------
    # 7C. PREVIOUS AND NEXT BUTTONS
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Previous Question"):

            if current_question > 0:

                # Save code answer before navigating
                if current_question < 2:
                    st.session_state.answers[current_question] = answer

                st.session_state.current_question -= 1

                st.session_state.audio_key += 1

                st.session_state.temp_transcript = ""

                st.rerun()

    with col2:

        if st.button("Next Question"):

            # Save current code answer
            if current_question < 2:
                st.session_state.answers[current_question] = answer

            # Move to next question
            if current_question < total_questions - 1:

                st.session_state.current_question += 1

                st.session_state.audio_key += 1

                st.session_state.temp_transcript = ""

                st.rerun()

            else:

                # Last question completed
                st.session_state.stage = "results"

                st.rerun()


# ==================================================
# 8. RESULTS STAGE
# ==================================================

if st.session_state.stage == "results":

    st.subheader("🏆 Interview Completed")

    total_questions = len(
        st.session_state.questions
    )

    total_score = 0

    if total_questions == 0:

        st.warning("No questions were evaluated.")

        st.stop()

    # Evaluate each question
    for i, question in enumerate(
        st.session_state.questions
    ):

        st.subheader(f"Question {i + 1}")

        # Display question
        st.write(question)

        # Retrieve answer
        answer = st.session_state.answers.get(
            i,
            ""
        )

        st.write("Answer:")

        st.write(
            answer if answer else "No answer provided"
        )

        # --------------------------------------------------
        # Handle unanswered questions
        # --------------------------------------------------

        if not answer.strip():

            evaluation = (
                "Result: Not Answered\n\n"
                "Score: 0/10\n\n"
                "Feedback: No response was provided.\n\n"
                "Improvement: Attempt the question "
                "to receive an evaluation."
            )

            st.session_state.evaluations[i] = evaluation
            st.session_state.scores[i] = 0

        # --------------------------------------------------
        # Evaluate answered questions
        # --------------------------------------------------

        elif i not in st.session_state.evaluations:

            try:

                with st.spinner(
                    f"Evaluating answer {i + 1}..."
                ):

                    evaluation = evaluate_answer(
                        question,
                        answer,
                        i
                    )

                st.session_state.evaluations[i] = evaluation

                # Extract score
                score = 0

                match = re.search(
                    r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10",
                    evaluation,
                    re.IGNORECASE
                )

                if match:

                    score = float(match.group(1))

                    # Keep score within 0-10
                    score = max(0, min(score, 10))

                st.session_state.scores[i] = score

            except Exception as e:

                st.session_state.evaluations[i] = (
                    f"Evaluation failed: {e}"
                )

                st.session_state.scores[i] = 0

        # --------------------------------------------------
        # Display evaluation
        # --------------------------------------------------

        st.info("Evaluation:")

        st.write(
            st.session_state.evaluations[i]
        )

        # Add score to total
        total_score += st.session_state.scores.get(
            i,
            0
        )

        st.divider()

    # ==================================================
    # 9. FINAL SCORE
    # ==================================================

    percentage = (
        total_score / (total_questions * 10)
    ) * 100

    st.subheader("Final Interview Results")

    st.metric(
        "Overall Score",
        f"{percentage:.1f}%"
    )

    st.write(
        f"Total Score: {total_score:.1f} / "
        f"{total_questions * 10}"
    )

    # ==================================================
    # 10. RESTART INTERVIEW
    # ==================================================

    if st.button("Start New Interview"):

        st.session_state.stage = "setup"

        st.session_state.questions = []
        st.session_state.current_question = 0

        st.session_state.answers = {}
        st.session_state.skills = []
        st.session_state.projects = []
        st.session_state.experience = []

        st.session_state.evaluations = {}
        st.session_state.scores = {}

        st.session_state.temp_transcript = ""
        st.session_state.audio_key += 1

        st.rerun()
