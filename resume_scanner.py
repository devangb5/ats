import streamlit as st
import pdfplumber
import io
import json
import base64
import spacy
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity

# Download NLP resources
nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")

# Streamlit UI
st.set_page_config(page_title="ATS Resume Scanner", layout="wide")
st.title("📄 AI-Powered ATS Resume Scanner")

st.write("🚀 Upload your Resume and Job Description to check compatibility")

uploaded_resume = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste the Job Description here")

# Function to extract text from PDF (Multi-Page Support)
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text

# Function to preprocess text
def preprocess_text(text):
    text = text.lower()
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(tokens)

# Compute job match score
def compute_match_score(resume_text, job_text):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    similarity_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return round(similarity_score * 100, 2)

# Find missing keywords (Categorized)
def find_missing_keywords(resume_text, job_text):
    job_tokens = set(word_tokenize(job_text))
    resume_tokens = set(word_tokenize(resume_text))
    missing_keywords = job_tokens - resume_tokens

    # Categorizing missing keywords
    categorized_keywords = {
        "Technical Skills": [],
        "Analytical Skills": [],
        "Soft Skills": []
    }

    for word in missing_keywords:
        if "programming" in word or "software" in word or "technical" in word:
            categorized_keywords["Technical Skills"].append(word)
        elif "analysis" in word or "problem-solving" in word:
            categorized_keywords["Analytical Skills"].append(word)
        else:
            categorized_keywords["Soft Skills"].append(word)

    return categorized_keywords

# Resume Formatting Check
def resume_format_feedback(resume_text):
    lines = resume_text.split("\n")
    bullet_points = sum(1 for line in lines if line.strip().startswith(("-", "•", "*")))
    word_count = len(resume_text.split())
s
    feedback = []
    if bullet_points < 5:
        feedback.append("🔹 Use more bullet points for better readability.")
    if word_count < 250:
        feedback.append("🔹 Resume is too short. Try adding more details.")
    elif word_count > 1000:
        feedback.append("🔹 Resume is too long. Consider summarizing content.")
    
    return feedback

# Resume Analysis Button
if st.button("Analyze Resume"):
    if uploaded_resume and job_description:
        with st.spinner("Analyzing Resume..."):
            resume_text = extract_text_from_pdf(uploaded_resume)

            if not resume_text:
                st.error("⚠️ Could not extract text from this PDF. Try another format.")
                st.stop()

            resume_clean = preprocess_text(resume_text)
            job_clean = preprocess_text(job_description)
            
            match_score = compute_match_score(resume_clean, job_clean)
            missing_keywords = find_missing_keywords(resume_clean, job_clean)
            formatting_feedback = resume_format_feedback(resume_text)

            # Display results
            st.success("✅ Analysis Complete!")
            st.subheader(f"🎯 Resume Match Score: {match_score}%")

            if match_score > 80:
                st.success("👍 Strong match! Your resume aligns well with the job description.")
            elif match_score > 50:
                st.warning("⚠️ Moderate match. Consider adding more relevant skills.")
            else:
                st.error("❌ Weak match. Significant improvements needed.")

            # Show missing keywords
            st.subheader("🔎 Missing Keywords")
            for category, words in missing_keywords.items():
                if words:
                    st.write(f"**{category}:** {', '.join(words)}")
                else:
                    st.write(f"✅ No missing {category} detected!")

            # Show resume formatting feedback
            st.subheader("📌 Resume Formatting Feedback")
            for feedback in formatting_feedback:
                st.write(feedback)

            # Download Analysis as Report
            analysis_data = f"""
            Resume Match Score: {match_score}%
            Missing Keywords:
            - Technical Skills: {", ".join(missing_keywords["Technical Skills"])}
            - Analytical Skills: {", ".join(missing_keywords["Analytical Skills"])}
            - Soft Skills: {", ".join(missing_keywords["Soft Skills"])}

            Resume Formatting Feedback:
            {''.join(['- ' + fb + '\\n' for fb in formatting_feedback])}
            """
            b64 = base64.b64encode(analysis_data.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="resume_analysis.txt">📥 Download Analysis Report</a>'
            st.markdown(href, unsafe_allow_html=True)

    else:
        st.error("⚠️ Please upload a resume and paste a job description.")

