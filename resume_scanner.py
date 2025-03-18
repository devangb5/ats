import streamlit as st
import pdfplumber
import io
import base64
import json
import spacy
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity

# Download nltk resources
nltk.download('punkt')

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Streamlit UI
st.set_page_config(page_title="ATS Resume Scanner", layout="wide")
st.title("📄 ATS Resume Scanner - Optimize Your Resume for Job Applications")

st.subheader("Upload your Resume & Job Description to check compatibility")

uploaded_resume = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste the Job Description here")

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text

# Function to preprocess text
def preprocess_text(text):
    text = text.lower()
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(tokens)

# Function to compute job match score
def compute_match_score(resume_text, job_text):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    similarity_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return round(similarity_score * 100, 2)

# Function to find missing keywords
def find_missing_keywords(resume_text, job_text):
    resume_tokens = set(word_tokenize(resume_text))
    job_tokens = set(word_tokenize(job_text))
    missing_keywords = job_tokens - resume_tokens
    return list(missing_keywords)

# Resume Analysis Button
if st.button("Analyze Resume"):
    if uploaded_resume and job_description:
        with st.spinner("Analyzing Resume..."):
            # Extract resume text
            resume_text = extract_text_from_pdf(uploaded_resume)
            
            # Preprocess text
            resume_clean = preprocess_text(resume_text)
            job_clean = preprocess_text(job_description)
            
            # Compute match score
            match_score = compute_match_score(resume_clean, job_clean)
            
            # Find missing keywords
            missing_keywords = find_missing_keywords(resume_clean, job_clean)
            
            # Display results
            st.success("✅ Analysis Complete!")
            st.subheader(f"🎯 Resume Match Score: {match_score}%")
            
            if match_score > 80:
                st.success("👍 Your resume is a strong match for this job!")
            elif match_score > 50:
                st.warning("⚠️ Your resume is a moderate match. Consider adding missing skills.")
            else:
                st.error("❌ Your resume needs improvement for this job.")

            st.subheader("🔎 Missing Keywords")
            if missing_keywords:
                st.write(", ".join(missing_keywords))
            else:
                st.write("✅ No missing keywords detected!")

            # Allow download of analysis
            analysis_data = f"""
            Resume Match Score: {match_score}%
            Missing Keywords: {", ".join(missing_keywords)}
            """
            b64 = base64.b64encode(analysis_data.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="resume_analysis.txt">📥 Download Analysis Report</a>'
            st.markdown(href, unsafe_allow_html=True)

    else:
        st.error("⚠️ Please upload a resume and paste a job description.")

