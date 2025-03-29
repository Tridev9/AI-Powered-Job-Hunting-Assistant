import os
import streamlit as st
import google.generativeai as genai
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import PyPDF2
import io
import json
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Initialize all session state variables
def init_session_state():
    if 'search_triggered' not in st.session_state:
        st.session_state.search_triggered = False
    if 'search_time' not in st.session_state:
        st.session_state.search_time = None
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = {'skills': [], 'experience': 0, 'titles': [], 'education': [], 'certifications': []}
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'custom_skills' not in st.session_state:
        st.session_state.custom_skills = []
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'target_company' not in st.session_state:
        st.session_state.target_company = ""
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    if 'job_title' not in st.session_state:
        st.session_state.job_title = "Software Engineer"
    if 'resume_uploaded' not in st.session_state:
        st.session_state.resume_uploaded = False
    if 'optimized_resume' not in st.session_state:
        st.session_state.optimized_resume = ""
    if 'cover_letter' not in st.session_state:
        st.session_state.cover_letter = ""
    if 'interview_questions' not in st.session_state:
        st.session_state.interview_questions = ""
    if 'mock_interview' not in st.session_state:
        st.session_state.mock_interview = ""
    if 'company_research' not in st.session_state:
        st.session_state.company_research = ""
    if 'connections' not in st.session_state:
        st.session_state.connections = ""
    if 'outreach_template' not in st.session_state:
        st.session_state.outreach_template = ""

init_session_state()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize models and clients
gemini_model = genai.GenerativeModel('gemini-1.5-pro')
firecrawl_app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))

# Indian major cities
INDIAN_CITIES = [
    "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Gurgaon", "Noida",
    "Remote", "Anywhere"
]

# Job platforms with specific search URLs
JOB_PLATFORMS = {
    "Naukri": {
        "url": "https://www.naukri.com",
        "search_pattern": "/{job_title}-jobs-in-{location}?experience={experience}"
    },
    "Indeed": {
        "url": "https://www.indeed.com",
        "search_pattern": "/jobs?q={job_title}&l={location}&explvl={experience_level}"
    },
    "Monster": {
        "url": "https://www.monsterindia.com",
        "search_pattern": "/search/{job_title}-jobs-in-{location}?exp={experience}"
    },
    "LinkedIn": {
        "url": "https://www.linkedin.com/jobs",
        "search_pattern": "/search/?keywords={job_title}&location={location}&f_E={experience_code}"
    },
    "PayScale": {
        "url": "https://www.payscale.com",
        "search_pattern": "/research/IN/Job={job_title}/Salary"
    }
}

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF resume with enhanced error handling"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""  # Handle None returns
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_skills_from_resume(resume_text):
    """Use Gemini 1.5 Pro to extract skills with structured output"""
    prompt = """Extract the following information from the resume in JSON format:
    {
        "technical_skills": [],
        "soft_skills": [],
        "years_experience": float,
        "job_titles": [],
        "education": [],
        "certifications": []
    }
    
    Resume Text:
    """ + resume_text[:10000]  # Using 1.5 Pro's larger context window
    
    try:
        response = gemini_model.generate_content(prompt)
        if response.text:
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                st.error("Failed to parse skills data")
        return {"technical_skills": [], "soft_skills": [], "years_experience": 0, "job_titles": [], "education": [], "certifications": []}
    except Exception as e:
        st.error(f"Error extracting skills: {str(e)}")
        return {"technical_skills": [], "soft_skills": [], "years_experience": 0, "job_titles": [], "education": [], "certifications": []}

def analyze_job_with_gemini(job_details, user_profile):
    """Enhanced analysis with Gemini 1.5 Pro"""
    prompt = f"""
    Analyze this job opportunity against the candidate profile and provide:
    1. Match score (0-100) with detailed breakdown
    2. Key strengths and weaknesses
    3. Missing qualifications
    4. Salary benchmarking (current market rates)
    5. Company culture insights
    6. Customized application strategy
    
    Format your response as markdown with these sections:
    
    ### 🎯 Match Analysis
    - Overall Score: [score]/100
    - Skills Match: [x]/[y] skills matched
    - Experience: [analysis]
    
    ### 💪 Strengths
    - [List candidate strengths for this role]
    
    ### 📉 Weaknesses
    - [List potential gaps]
    
    ### 💰 Salary Insights
    - [Market range analysis]
    
    ### 🏢 Company Fit
    - [Culture analysis]
    
    ### 📝 Application Strategy
    - [Customized tips]
    
    Job Details:
    {json.dumps(job_details, indent=2)}
    
    Candidate Profile:
    {json.dumps(user_profile, indent=2)}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error analyzing with Gemini: {str(e)}")
        return None

def optimize_resume(resume_text, job_description):
    """Optimize resume based on job description"""
    prompt = f"""
    Optimize this resume for the following job description. Provide:
    1. ATS-optimized version with relevant keywords
    2. Improved formatting and structure
    3. Enhanced bullet points with quantifiable achievements
    4. Skills section reordered by relevance
    
    Return the optimized resume in markdown format.
    
    Job Description:
    {job_description}
    
    Original Resume:
    {resume_text}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error optimizing resume: {str(e)}")
        return None

def generate_cover_letter(resume_text, job_description, company_name):
    """Generate tailored cover letter"""
    prompt = f"""
    Write a professional cover letter for this job application.
    Tailor it specifically to the company and job description.
    Include:
    1. Personalized opening
    2. 3-4 key qualifications
    3. Specific examples from resume
    4. Enthusiastic closing
    
    Job Description:
    {job_description}
    
    Company Name:
    {company_name}
    
    Candidate Resume:
    {resume_text}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        return None

def suggest_ats_keywords(job_description):
    """Extract ATS keywords from job description"""
    prompt = f"""
    Extract the most important keywords for Applicant Tracking Systems (ATS)
    from this job description. Return only a comma-separated list.
    
    Job Description:
    {job_description}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return [kw.strip() for kw in response.text.split(",") if kw.strip()]
    except Exception as e:
        st.error(f"Error extracting keywords: {str(e)}")
        return []

def generate_interview_questions(job_description):
    """Generate potential interview questions"""
    prompt = f"""
    Generate 10 likely interview questions for this job,
    including 5 technical and 5 behavioral questions.
    Format as a numbered list with question type.
    
    Job Description:
    {job_description}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None

def conduct_mock_interview(questions, resume_text):
    """AI-powered mock interview"""
    prompt = f"""
    Conduct a mock interview with the candidate.
    Ask one question at a time and evaluate responses.
    Provide constructive feedback after each answer.
    
    Questions:
    {questions}
    
    Candidate Resume:
    {resume_text}
    
    Start with the first question.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error conducting mock interview: {str(e)}")
        return None

def generate_company_research(company_name):
    """Generate company research report"""
    prompt = f"""
    Create a comprehensive research report about this company
    to help a job candidate prepare for interviews.
    Include:
    1. Company overview
    2. Recent news
    3. Company culture
    4. Interview tips specific to this company
    
    Company Name:
    {company_name}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating research: {str(e)}")
        return None

def suggest_linkedin_connections(company_name, job_title):
    """Suggest relevant LinkedIn connections"""
    prompt = f"""
    Suggest types of LinkedIn connections to make when applying
    to this company for this position. Include:
    1. Relevant job titles to connect with
    2. Recommended outreach approach
    3. Icebreaker message templates
    
    Company: {company_name}
    Position: {job_title}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating connection suggestions: {str(e)}")
        return None

def generate_outreach_template(connection_type, company_name):
    """Generate personalized outreach template"""
    prompt = f"""
    Create a personalized LinkedIn outreach message template
    for connecting with {connection_type} at {company_name}.
    Make it professional but friendly.
    Include:
    1. Personalized greeting
    2. Reason for connecting
    3. Specific compliment or commonality
    4. Clear call-to-action
    
    Return only the message content.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating template: {str(e)}")
        return None

def generate_search_url(platform, job_title, location, experience):
    """Generate platform-specific job search URLs with proper parameters"""
    platform_data = JOB_PLATFORMS.get(platform)
    if not platform_data:
        return None
    
    # Clean inputs
    clean_job_title = job_title.strip().lower().replace(' ', '-')
    clean_location = location.strip().lower().replace(' ', '-')
    
    # Platform-specific parameter handling
    if platform == "Naukri":
        return f"{platform_data['url']}/{clean_job_title}-jobs-in-{clean_location}?experience={experience}"
    elif platform == "Indeed":
        if experience < 1:
            exp_level = "entry_level"
        elif experience < 3:
            exp_level = "mid_level"
        else:
            exp_level = "senior_level"
        return f"{platform_data['url']}/jobs?q={clean_job_title}&l={clean_location}&explvl={exp_level}"
    elif platform == "Monster":
        return f"{platform_data['url']}/search/{clean_job_title}-jobs-in-{clean_location}?exp={experience}-{experience+2}"
    elif platform == "LinkedIn":
        if experience < 2:
            exp_code = "1"
        elif experience < 5:
            exp_code = "2"
        elif experience < 10:
            exp_code = "3"
        else:
            exp_code = "4"
        return f"{platform_data['url']}/search/?keywords={clean_job_title}&location={clean_location}&f_E={exp_code}"
    elif platform == "PayScale":
        return f"{platform_data['url']}/research/IN/Job={clean_job_title}/Salary"
    return None

def search_jobs(job_title, locations, experience, skills, platforms):
    """Search for jobs across multiple platforms"""
    try:
        results = []
        
        for platform in platforms:
            for location in locations:
                search_url = generate_search_url(platform, job_title, location, experience)
                if not search_url:
                    continue
                
                try:
                    # Simulated response for demo
                    scraped_data = {
                        "title": f"{job_title} ({platform})",
                        "company": f"Sample Company {len(results)+1}",
                        "location": location,
                        "experience": f"{experience}+ years",
                        "skills": skills[:3] + [f"{platform}-Specialized"],
                        "salary": f"₹{10+len(results)*2}-{15+len(results)*3} LPA",
                        "url": search_url,
                        "platform": platform,
                        "posted_date": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Calculate relevance score
                    skills_match = len(set(skills) & set(scraped_data["skills"])) / len(scraped_data["skills"]) * 100
                    exp_match = 100 - abs(experience - int(scraped_data["experience"].split("+")[0])) * 10
                    scraped_data["match_score"] = min(100, (skills_match * 0.7 + exp_match * 0.3))
                    
                    results.append(scraped_data)
                
                except Exception as e:
                    st.error(f"Error searching {platform}: {str(e)}")
        
        return sorted(results, key=lambda x: (-x["match_score"], x["platform"]))
    except Exception as e:
        st.error(f"Job search failed: {str(e)}")
        return []

def get_industry_trends(industry, location):
    """Get comprehensive industry trends using Gemini"""
    prompt = f"""
    Provide a detailed industry trends report for {industry} professionals in {location}.
    Include these sections with specific data:
    
    ### 💰 Salary Trends
    - Entry-level: [range]
    - Mid-career: [range]
    - Senior-level: [range]
    - Factors affecting compensation
    
    ### 📈 In-Demand Skills
    1. Technical skills:
       - [List 5-7 skills]
    2. Soft skills:
       - [List 3-5 skills]
    
    ### 🏆 Top Companies
    - [List 5-7 top employers]
    - Notable perks/benefits
    
    ### 🚀 Emerging Technologies
    - [List 3-5 emerging tech]
    - Adoption trends
    
    ### 📅 Hiring Trends
    - Best times to apply
    - Growth projections
    - Remote work availability
    
    Format the response in markdown with clear headings.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error getting industry trends: {str(e)}")
        return "Industry trends data unavailable."

# Streamlit UI Configuration
st.set_page_config(
    page_title="AI Job Hunting Assistant Pro+",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main App Title
st.title("🚀 AI Job Hunting Assistant Pro+")
st.markdown("The ultimate all-in-one job search toolkit ")

# Global Resume Upload in Sidebar
with st.sidebar:
    st.header("📄 Resume Upload")
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type="pdf", key="global_resume_uploader")
    
    if uploaded_file and (uploaded_file != st.session_state.uploaded_file):
        with st.spinner("Analyzing resume..."):
            st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
            if st.session_state.resume_text:
                st.session_state.resume_data = extract_skills_from_resume(st.session_state.resume_text)
                st.session_state.uploaded_file = uploaded_file
                st.session_state.resume_uploaded = True
                st.success("Resume analyzed successfully!")
            else:
                st.error("Failed to process resume")

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Job Search", "📝 Resume Tools", "💼 Interview Prep", "🤝 Networking"])

with tab1:  # Job Search Tab
    st.header("🔍 Job Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.job_title = st.text_input("Job Title", st.session_state.job_title)
        locations = st.multiselect("Preferred Locations", INDIAN_CITIES, ["Bangalore", "Remote"])
        platforms = st.multiselect("Job Platforms", list(JOB_PLATFORMS.keys()), ["Naukri", "LinkedIn"])
        
        # Experience - auto-filled from resume if available
        if st.session_state.resume_data.get('years_experience', 0) > 0:
            experience = st.slider("Years of Experience", 0, 30, int(st.session_state.resume_data['years_experience']))
        else:
            experience = st.slider("Years of Experience", 0, 30, 3)
        
        # Skills - with enhanced "Other" option
        base_skills = st.session_state.resume_data.get('technical_skills', []) + st.session_state.resume_data.get('soft_skills', [])
        if not base_skills:
            base_skills = ["Python", "Java", "SQL", "Machine Learning"]
        
        selected_skills = st.multiselect("Your Skills", base_skills + ["Other..."], default=base_skills)
        
        if "Other..." in selected_skills:
            custom_skill = st.text_input("Add custom skill")
            if custom_skill and st.button("Add Skill"):
                if custom_skill not in st.session_state.custom_skills:
                    st.session_state.custom_skills.append(custom_skill)
                selected_skills = [s for s in selected_skills if s != "Other..."] + [custom_skill]
        
        # Add any previously custom skills
        selected_skills += [s for s in st.session_state.custom_skills if s not in selected_skills]
    
    with col2:
        st.session_state.job_description = st.text_area("Paste Job Description (for optimization)", st.session_state.job_description, height=200)
        st.session_state.target_company = st.text_input("Target Company (for research)", st.session_state.target_company)
        
        if st.button("🚀 Start Smart Search", use_container_width=True, type="primary"):
            st.session_state.search_triggered = True
            st.session_state.search_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Display search results
    if st.session_state.search_triggered:
        with st.spinner(f"Searching across {len(platforms)} platforms..."):
            jobs = search_jobs(st.session_state.job_title, locations, experience, selected_skills, platforms)
        
        if jobs:
            time_display = f"(Updated: {st.session_state.search_time})" if st.session_state.search_time else ""
            st.success(f"Found {len(jobs)} matching jobs {time_display}")
            
            # Display in tabs by platform
            tab_names = list({job['platform'] for job in jobs})
            tabs = st.tabs([f"{platform} 🔍" for platform in tab_names])
            
            platform_tabs = {platform: tab for platform, tab in zip(tab_names, tabs)}
            
            for job in sorted(jobs, key=lambda x: -x['match_score']):
                with platform_tabs[job['platform']]:
                    with st.expander(f"🌟 {job['match_score']:.0f}% | {job['title']} at {job['company']} | {job['location']} | 💰 {job['salary']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"""
                            **📌 Position:** {job['title']}  
                            **🏢 Company:** {job['company']}  
                            **📍 Location:** {job['location']}  
                            **📅 Experience:** {job['experience']}  
                            **💰 Salary Range:** {job['salary']}  
                            **🛠️ Key Skills:** {", ".join(job['skills'])}  
                            **📅 Posted:** {job.get('posted_date', 'Recently')}
                            """)
                            
                            st.link_button("View Job Posting", job['url'])
                        
                        with col2:
                            if st.button("🤖 AI Analysis", key=f"analyze_{job['url']}"):
                                user_profile = {
                                    "experience": experience,
                                    "skills": selected_skills,
                                    "resume_titles": st.session_state.resume_data.get('job_titles', []),
                                    "resume_skills": base_skills
                                }
                                with st.spinner("Generating deep analysis..."):
                                    analysis = analyze_job_with_gemini(job, user_profile)
                                    st.session_state[f'analysis_{job["url"]}'] = analysis
                        
                        if f'analysis_{job["url"]}' in st.session_state:
                            st.markdown("---")
                            st.markdown(st.session_state[f'analysis_{job["url"]}'])
            
            # Industry Insights Section
            st.header("📊 Market Intelligence")
            with st.spinner("Generating industry insights..."):
                trends = get_industry_trends(st.session_state.job_title.split()[0], locations[0])
                st.markdown(trends)
        else:
            st.warning("No matching jobs found. Try adjusting your search criteria.")

with tab2:  # Resume Tools Tab
    st.header("📝 Resume Optimization Toolkit")
    
    if st.session_state.resume_uploaded and st.session_state.resume_text:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Resume")
            st.text_area("Original Resume Content", st.session_state.resume_text, height=400, disabled=True)
        
        with col2:
            st.subheader("Optimized Version")
            if st.session_state.job_description:
                if st.button("✨ Optimize Resume"):
                    with st.spinner("Enhancing your resume..."):
                        st.session_state.optimized_resume = optimize_resume(st.session_state.resume_text, st.session_state.job_description)
                
                if st.session_state.optimized_resume:
                    st.markdown(st.session_state.optimized_resume)
                    st.download_button(
                        "Download Optimized Resume",
                        st.session_state.optimized_resume,
                        file_name="optimized_resume.md"
                    )
                
                st.subheader("ATS Keywords")
                keywords = suggest_ats_keywords(st.session_state.job_description)
                st.write("Important keywords to include:")
                st.write(", ".join(keywords))
            else:
                st.warning("Please enter a job description in the Job Search tab")
            
            st.subheader("Cover Letter Generator")
            if st.session_state.target_company:
                if st.button("✍️ Generate Cover Letter"):
                    with st.spinner("Crafting your perfect cover letter..."):
                        st.session_state.cover_letter = generate_cover_letter(
                            st.session_state.resume_text,
                            st.session_state.job_description,
                            st.session_state.target_company
                        )
                
                if st.session_state.cover_letter:
                    st.markdown(st.session_state.cover_letter)
                    st.download_button(
                        "Download Cover Letter",
                        st.session_state.cover_letter,
                        file_name="cover_letter.md"
                    )
            else:
                st.warning("Please enter a target company in the Job Search tab")
    else:
        st.warning("Please upload your resume using the sidebar uploader")

with tab3:  # Interview Prep Tab
    st.header("💼 Interview Preparation")
    
    if st.session_state.resume_uploaded and st.session_state.resume_text:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Potential Interview Questions")
            if st.session_state.job_description:
                if st.button("🧠 Generate Questions"):
                    with st.spinner("Creating relevant questions..."):
                        st.session_state.interview_questions = generate_interview_questions(st.session_state.job_description)
                
                if st.session_state.interview_questions:
                    st.markdown(st.session_state.interview_questions)
            else:
                st.warning("Please enter a job description in the Job Search tab")
        
        with col2:
            st.subheader("Mock Interview")
            if st.session_state.interview_questions:
                if st.button("🎤 Start Mock Interview"):
                    with st.spinner("Setting up your interview..."):
                        st.session_state.mock_interview = conduct_mock_interview(
                            st.session_state.interview_questions,
                            st.session_state.resume_text
                        )
                
                if st.session_state.mock_interview:
                    st.markdown(st.session_state.mock_interview)
            else:
                st.warning("Please generate questions first")
        
        st.subheader("Company Research")
        if st.session_state.target_company:
            if st.button("🏢 Generate Company Report"):
                with st.spinner("Researching company..."):
                    st.session_state.company_research = generate_company_research(st.session_state.target_company)
            
            if st.session_state.company_research:
                st.markdown(st.session_state.company_research)
        else:
            st.warning("Please enter a target company in the Job Search tab")
    else:
        st.warning("Please upload your resume using the sidebar uploader")

with tab4:  # Networking Tab
    st.header("🤝 Networking Toolkit")
    
    if st.session_state.resume_uploaded:
        if st.session_state.target_company and st.session_state.job_title:
            st.subheader("LinkedIn Connection Suggestions")
            if st.button("👥 Get Connection Suggestions"):
                with st.spinner("Finding relevant connections..."):
                    st.session_state.connections = suggest_linkedin_connections(
                        st.session_state.target_company,
                        st.session_state.job_title
                    )
            
            if st.session_state.connections:
                st.markdown(st.session_state.connections)
            
            st.subheader("Outreach Templates")
            connection_type = st.selectbox(
                "Select connection type",
                ["Hiring Manager", "Team Member", "Recruiter", "Alumni", "Industry Peer"],
                key="conn_type"
            )
            
            if st.button("📩 Generate Outreach Message"):
                with st.spinner("Creating template..."):
                    st.session_state.outreach_template = generate_outreach_template(
                        connection_type,
                        st.session_state.target_company
                    )
            
            if st.session_state.outreach_template:
                customized_message = st.text_area(
                    "Customize your outreach message:", 
                    st.session_state.outreach_template, 
                    height=200,
                    key="outreach_msg"
                )
                if st.button("💾 Save Customized Message"):
                    st.session_state.outreach_template = customized_message
                    st.success("Message saved! Copy it to LinkedIn")
        else:
            st.warning("Please enter target company and job title in the Job Search tab")
    else:
        st.warning("Please upload your resume using the sidebar uploader")

# Footer
st.markdown("---")
st.caption("""
ℹ️ AI Job Hunting Assistant Pro+ v2.0 
🔒 Your data is processed securely and not stored permanently
""")
