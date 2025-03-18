import streamlit as st
import pdf2image
import io
import json
import base64
import google.generativeai as genai
from fpdf import FPDF
import pdfminer.high_level  # Import pdfminer to extract text from PDF

# Ensure the API key is correctly stored in secrets.toml
api_key = st.secrets["API_KEY"]  # Accessing the API key
genai.configure(api_key=api_key)  # Configuring the Generative AI with the API key
model = genai.GenerativeModel('gemini-2.0-flash')

# Define cached functions
@st.cache_data()
def get_gemini_response(input, pdf_content, prompt):
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

@st.cache_data()
def get_gemini_response_keywords(input, pdf_content, prompt):
    response = model.generate_content([input, pdf_content[0], prompt])
    return json.loads(response.text[8:-4])

@st.cache_data()
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

@st.cache_data()
def extract_text_from_pdf(uploaded_file):
    """Extract text from the uploaded PDF file."""
    if uploaded_file is not None:
        text = pdfminer.high_level.extract_text(uploaded_file)
        return text
    else:
        raise FileNotFoundError("No file uploaded")

def generate_pdf_report(resume_analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in resume_analysis:
        pdf.cell(200, 10, txt=line, ln=True)

    pdf_file = io.BytesIO()
    pdf.output(pdf_file)
    pdf_file.seek(0)
    return pdf_file

def generate_recommendations(missing_skills, experience_assessment, cultural_fit_assessment):
    recommendations = []

    if missing_skills:
        recommendations.append("Consider adding the following skills to your resume: " + ", ".join(missing_skills))
    else:
        recommendations.append("Great job! You have all the key skills required for this position.")

    if experience_assessment:
        recommendations.append("Enhance your experience section by including specific achievements related to the following: " + ", ".join(experience_assessment))

    if cultural_fit_assessment:
        recommendations.append("Highlight examples of your work style and values that align with the company's culture. Consider emphasizing your strengths in: " + ", ".join(cultural_fit_assessment))

    return recommendations

def suggest_job_titles(resume_text):
    """Generate relevant job titles based on the resume text using AI."""
    prompt = f"Based on the following resume content, suggest relevant job titles:\n\n{resume_text}\n\nSuggested job titles:"
    response = model.generate_content([prompt])
    return response.text.strip()

# Streamlit App
st.set_page_config(page_title="ATS Resume Scanner")
st.header("Application Tracking System")
input_text = st.text_area("Job Description: ", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if 'resume' not in st.session_state:
    st.session_state.resume = None

ats_text = None  # Initialize ats_text
response = None  # Initialize response

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")
    st.session_state.resume = uploaded_file

    # Extract and display resume text
    resume_text = extract_text_from_pdf(uploaded_file)
    st.text_area("Extracted Resume Text", value=resume_text, height=300)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    submit1 = st.button("Tell Me About the Resume")

with col2:
    submit2 = st.button("Get Keywords")

with col3:
    submit3 = st.button("Percentage Match")

# New buttons for ATS and Recruiter views
col4, col5 = st.columns(2, gap="medium")

with col4:
    submit_ats = st.button("Show ATS View")

with col5:
    submit_recruiter = st.button("Show Recruiter View")

# Define the prompts
input_prompt1 = """ You are an experienced Technical Human Resource Manager, your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements."""

input_prompt2 = """ As an expert ATS (Applicant Tracking System) scanner with an in-depth understanding of AI and ATS functionality, 
your task is to evaluate a resume against a provided job description. Please identify the specific skills and keywords 
necessary to maximize the impact of the resume and provide response in JSON format as {Technical Skills:[], Analytical Skills:[], Soft Skills:[]}.
Note: Please do not make up the answer only answer from the job description provided."""

input_prompt3 = """ You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First the output should come as percentage and then keywords missing and last final thoughts."""

# Additional prompts
input_prompt4 = """ As an HR professional, your task is to analyze the provided resume in relation to the job description. 
Evaluate the candidate's overall experience based on the years of experience, relevance of previous roles, 
and specific achievements that align with the job requirements. 
Provide a summary of how well the candidate’s experience matches the job position."""

input_prompt5 = """ You are an expert in organizational culture and team dynamics. 
Assess the provided resume against the job description and identify how well the candidate fits into the company's culture. 
Consider factors such as work style, values, and previous work environments that may influence their fit. 
Provide a detailed analysis of the candidate’s potential cultural fit."""

input_prompt6 = """ As an experienced recruiter, evaluate the provided resume in relation to the job description to identify the soft skills demonstrated. 
Highlight the candidate's communication skills, teamwork, adaptability, and problem-solving abilities. 
Discuss how these skills may impact their success in the role."""

input_prompt7 = """ As an education specialist, review the candidate’s educational background and certifications against the job description. 
Discuss the relevance of their degrees, any certifications that may enhance their candidacy, and how their educational qualifications align with the role."""

input_prompt8 = """ Analyze the candidate’s career progression as outlined in the resume. 
Consider the trajectory of their career, promotions, and transitions between roles. 
Discuss whether their career path indicates growth and alignment with the job they are applying for."""

input_prompt9 = """ Assess the technical skills listed on the resume against the job description. 
Identify any key technical skills required for the position and evaluate how well the candidate meets these requirements. 
Provide a summary of the candidate's technical abilities and any gaps that may exist."""

input_prompt10 = """ Based on the analysis of the provided resume and job description, provide an overall recommendation for the candidate. 
State whether the candidate should be shortlisted for an interview and justify your recommendation with key points from your analysis."""

# Handling resume analysis
if submit1:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt1, pdf_content, input_text)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.write("Please upload the resume")

elif submit2:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response_keywords(input_prompt2, pdf_content, input_text)
        st.subheader("Skills are:")
        if response is not None:
            st.write(f"Technical Skills: {', '.join(response['Technical Skills'])}.")
            st.write(f"Analytical Skills: {', '.join(response['Analytical Skills'])}.")
            st.write(f"Soft Skills: {', '.join(response['Soft Skills'])}.")
    else:
        st.write("Please upload the resume")

elif submit3:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt3, pdf_content, input_text)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.write("Please upload the resume")

# Show ATS view
if submit_ats:
    if st.session_state.resume is not None:
        ats_text = extract_text_from_pdf(st.session_state.resume)
        st.subheader("ATS View")
        st.text_area("ATS sees:", ats_text, height=300)
    else:
        st.write("Please upload the resume")

# Show Recruiter view
if submit_recruiter:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt1, pdf_content, input_text)
        st.subheader("Recruiter View")
        st.write("Here’s how the resume appears to a recruiter:")
        st.write(response)
    else:
        st.write("Please upload the resume")

# Job Title Suggestions
if st.button("Suggest Relevant Job Titles"):
    if st.session_state.resume is not None:
        job_titles = suggest_job_titles(resume_text)
        st.subheader("Suggested Job Titles")
        if job_titles:
            st.write(job_titles)
        else:
            st.write("No relevant job titles found.")
    else:
        st.write("Please upload the resume first.")

# Recommendations Section
if st.button("Generate Recommendations"):
    if st.session_state.resume is not None:
        # Evaluate missing skills and generate recommendations
        job_description = input_text
        if job_description and ats_text:
            skills_evaluation = get_gemini_response_keywords(input_prompt2, input_pdf_setup(st.session_state.resume), job_description)
            missing_skills = skills_evaluation.get('Technical Skills', [])
            experience_assessment = assess_experience(ats_text)
            cultural_fit_assessment = assess_cultural_fit(ats_text)
            recommendations = generate_recommendations(missing_skills, experience_assessment, cultural_fit_assessment)

            st.subheader("Improvement Recommendations")
            for rec in recommendations:
                st.write("- " + rec)
        else:
            st.warning("Please provide a job description to generate recommendations.")
    else:
        st.write("Please upload the resume first.")

# Additional Analysis Buttons
col6, col7, col8 = st.columns(3, gap="medium")

with col6:
    submit4 = st.button("Evaluate Candidate Experience")

with col7:
    submit5 = st.button("Assess Cultural Fit")

with col8:
    submit6 = st.button("Evaluate Soft Skills")

# Handling additional prompts
if submit4:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt4, pdf_content, input_text)
        st.subheader("Candidate Experience Evaluation")
        st.write(response)
    else:
        st.write("Please upload the resume")

if submit5:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt5, pdf_content, input_text)
        st.subheader("Cultural Fit Assessment")
        st.write(response)
    else:
        st.write("Please upload the resume")

if submit6:
    if st.session_state.resume is not None:
        pdf_content = input_pdf_setup(st.session_state.resume)
        response = get_gemini_response(input_prompt6, pdf_content, input_text)
        st.subheader("Soft Skills Evaluation")
        st.write(response)
    else:
        st.write("Please upload the resume")

# Download evaluation report functionality
if st.button("Download Evaluation Report"):
    if st.session_state.resume is not None and ats_text is not None and response is not None:
        report_content = [
            f"ATS View:\n{ats_text}\n\n",
            f"Recruiter View:\n{response}\n\n"
        ]
        report_pdf = generate_pdf_report(report_content)
        st.download_button(
            label="Download PDF Report",
            data=report_pdf,
            file_name="evaluation_report.pdf",
            mime="application/pdf"
        )
    else:
        st.write("Please complete all evaluations before downloading the report.")
