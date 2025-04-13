import os
import json
import logging
import random
import time
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables.")

class AIAnalyzer:
    """
    Class to handle AI-powered text analysis using OpenAI API.
    """
    def __init__(self):
        """Initialize the OpenAI client"""
        try:
            # Import OpenAI inside the method to handle any import errors gracefully
            try:
                from openai import OpenAI
                self.OpenAI = OpenAI
            except ImportError:
                logger.error("OpenAI package is not installed or cannot be imported")
                self.api_available = False
                return
                
            self.client = self.OpenAI(api_key=OPENAI_API_KEY)
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            self.model = "gpt-4o"
            # Set a more cost-effective fallback model if needed
            self.fallback_model = "gpt-3.5-turbo"
            self.api_available = True
            logger.info("AIAnalyzer initialized with OpenAI")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.api_available = False
    
    def analyze_job_description(self, text):
        """
        Analyze job description text to extract key information.
        
        Args:
            text: str, the job description text
            
        Returns:
            dict: Structured information about the job
        """
        if not self.api_available or not OPENAI_API_KEY:
            logger.warning("OpenAI API not available or API key missing, using fallback extraction")
            return self._extract_job_info_fallback(text)
        
        prompt = f"""
        Please analyze the following job description and extract key information in a structured format.
        
        Job Description:
        {text}
        
        Extract the following information:
        1. Job title/position
        2. Required skills and qualifications
        3. Preferred skills (if any)
        4. Required experience level
        5. Job responsibilities
        6. Company/team information
        7. A short summary of the position (max 100 words)
        
        Respond with a JSON object with the following keys:
        - position (string)
        - requirements (array of strings, max 8 items)
        - preferred_skills (array of strings)
        - experience_level (string)
        - responsibilities (array of strings, max 8 items)
        - company_info (string)
        - summary (string)
        """
        
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Try with primary model first
                current_model = self.model if retry_count == 0 else self.fallback_model
                
                logger.info(f"Attempting job description analysis with model: {current_model}")
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                # Parse the response
                jd_data = json.loads(response.choices[0].message.content)
                
                # Log successful analysis
                logger.info(f"Successfully analyzed job description: {jd_data.get('position', 'Unknown position')}")
                
                return jd_data
                
            except Exception as e:
                error_message = str(e)
                # Check error message for specific errors by string since we can't import the types
                if "Rate limit" in error_message or "insufficient_quota" in error_message:
                    logger.warning(f"Rate limit or quota error: {error_message}")
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.info(f"Retrying with fallback model, attempt {retry_count}")
                        time.sleep(1)  # Add a small delay before retrying
                    else:
                        logger.error("All retries failed due to rate limits")
                        return self._extract_job_info_fallback(text)
                        
                elif "api" in error_message.lower() or "connection" in error_message.lower():
                    logger.error(f"API error: {error_message}")
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(2)  # Slightly longer delay for API errors
                    else:
                        return self._extract_job_info_fallback(text)
                        
                elif "authentication" in error_message.lower() or "auth" in error_message.lower() or "key" in error_message.lower():
                    logger.error(f"Authentication error: {error_message}")
                    self.api_available = False
                    return self._extract_job_info_fallback(text)
                else:
                    # Any other errors
                    logger.error(f"Unexpected error analyzing job description: {error_message}")
                    return self._extract_job_info_fallback(text)
        
        # If we've exhausted retries
        return self._extract_job_info_fallback(text)
        
    def _extract_job_info_fallback(self, text):
        """
        Basic fallback method to extract job information when AI is unavailable
        
        Args:
            text: str, the job description text
            
        Returns:
            dict: Simple structured information about the job
        """
        logger.info("Using fallback extraction for job description")
        
        # Try to extract position using regex patterns
        position_pattern = r"(?:position|job title|role)\s*(?::|is|as)\s*(?:a|an)?\s*([A-Za-z\s]+(?:Developer|Engineer|Designer|Manager|Consultant|Specialist|Analyst|Director|Lead|Assistant))"
        position_match = re.search(position_pattern, text, re.IGNORECASE)
        
        position = "Unknown Position"
        if position_match:
            position = position_match.group(1).strip()
        else:
            # Try to find common job titles
            job_titles = [
                "Software Engineer", "Product Manager", "Data Scientist", 
                "Frontend Developer", "Backend Developer", "Full-Stack Developer",
                "DevOps Engineer", "UX Designer", "Project Manager", "QA Engineer"
            ]
            for title in job_titles:
                if title.lower() in text.lower():
                    position = title
                    break
                    
        # Extract requirements (look for bullet points after "requirements" section)
        requirements = []
        req_section = re.split(r"requirements|qualifications", text, flags=re.IGNORECASE)
        if len(req_section) > 1:
            req_text = req_section[1].split("\n", 10)[:10]  # Get first 10 lines after requirements
            for line in req_text:
                line = line.strip()
                if line and (line.startswith("•") or line.startswith("-") or line.startswith("*")):
                    requirements.append(line.strip("•-* "))
                elif len(line) > 15 and len(line) < 200:  # Reasonably sized lines might be requirements
                    requirements.append(line)
        
        # If no requirements found, extract sentences containing skill keywords
        if not requirements:
            skill_keywords = ["experience", "knowledge", "familiarity", "skill", "proficiency", "ability"]
            sentences = text.split(".")
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in skill_keywords):
                    requirements.append(sentence.strip())
                if len(requirements) >= 5:
                    break
                    
        # Limit to 8 items
        requirements = requirements[:8]
        
        # Create a basic summary (first paragraph or few sentences)
        summary_text = text.strip().split("\n\n")[0].replace("\n", " ")
        if len(summary_text) > 150:
            summary_text = summary_text[:147] + "..."
            
        return {
            "position": position,
            "requirements": requirements if requirements else ["Experience relevant to the position"],
            "preferred_skills": [],
            "experience_level": "Not specified",
            "responsibilities": ["Responsibilities related to " + position],
            "company_info": "Not specified",
            "summary": summary_text if summary_text else "Position description unavailable"
        }
    
    def analyze_cv(self, cv_text, job_description):
        """
        Analyze CV against job description to evaluate match.
        
        Args:
            cv_text: str, the CV text
            job_description: dict, parsed job description data
            
        Returns:
            dict: Candidate evaluation data
        """
        if not self.api_available or not OPENAI_API_KEY:
            logger.warning("OpenAI API not available or API key missing, using fallback CV analysis")
            return self._extract_cv_info_fallback(cv_text, job_description)
            
        # Prepare job description for comparison
        jd_position = job_description.get("position", "Not specified")
        jd_requirements = job_description.get("requirements", [])
        jd_responsibilities = job_description.get("responsibilities", [])
        jd_preferred_skills = job_description.get("preferred_skills", [])
        
        # Format requirements for the prompt
        formatted_requirements = "\n".join([f"- {req}" for req in jd_requirements])
        formatted_responsibilities = "\n".join([f"- {resp}" for resp in jd_responsibilities])
        
        prompt = f"""
        You're an AI recruitment assistant. Analyze the following resume/CV against a job description for {jd_position}.
        
        Resume/CV:
        {cv_text}
        
        Job Requirements:
        {formatted_requirements}
        
        Job Responsibilities:
        {formatted_responsibilities}
        
        Your task:
        1. Calculate a match score (0-100) based on how well the candidate matches the job requirements and responsibilities.
        2. Identify the candidate's top 3-5 strengths relative to this position.
        3. Identify 1-3 areas where the candidate might not meet the requirements.
        
        Format your response as a JSON object with the following structure:
        {{
          "match_score": number (0-100),
          "strengths": array of strings,
          "weaknesses": array of strings,
          "summary": string (brief assessment, max 100 words)
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            cv_analysis = json.loads(response.choices[0].message.content)
            
            # Ensure the match score is capped at 100
            if "match_score" in cv_analysis and cv_analysis["match_score"] > 100:
                cv_analysis["match_score"] = 100
            
            # Log successful analysis
            logger.info(f"Successfully analyzed CV. Match score: {cv_analysis.get('match_score', 0)}")
            
            return cv_analysis
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error analyzing CV: {error_message}")
            
            # Check for common error types
            if "quota" in error_message.lower() or "rate limit" in error_message.lower():
                logger.warning("API quota or rate limit exceeded")
            elif "key" in error_message.lower() or "auth" in error_message.lower():
                logger.error("API key authentication error")
                self.api_available = False
                
            # Return fallback analysis
            return self._extract_cv_info_fallback(cv_text, job_description)
            
    def _extract_cv_info_fallback(self, cv_text, job_description):
        """
        Basic fallback method for CV analysis when AI is unavailable
        
        Args:
            cv_text: str, the CV text
            job_description: dict, parsed job description data
            
        Returns:
            dict: Basic candidate evaluation data
        """
        logger.info("Using fallback CV analysis method")
        
        # Extract basic info using regex patterns
        from utils.document_parser import DocumentParser
        
        # Get name and email
        name = DocumentParser.extract_name(cv_text) or "Unknown Candidate"
        email = DocumentParser.extract_email(cv_text)
        
        # Get requirements from job description
        requirements = job_description.get("requirements", [])
        
        # Extract skills from CV
        skills = DocumentParser.extract_skills(cv_text)
        
        # Calculate a very basic match score
        match_score = 0
        matched_skills = []
        missing_skills = []
        
        if requirements and skills:
            # Count how many job requirements appear in candidate skills
            for req in requirements:
                found = False
                for skill in skills:
                    if skill.lower() in req.lower() or req.lower() in skill.lower():
                        found = True
                        matched_skills.append(skill)
                        break
                if not found:
                    missing_skills.append(req)
                    
            # Calculate a percentage score based on matched requirements
            match_score = int((len(matched_skills) / len(requirements)) * 80) if requirements else 50
            
            # Add bonus points for additional relevant skills
            additional_relevant_skills = len(skills) - len(matched_skills)
            if additional_relevant_skills > 0:
                match_score += min(additional_relevant_skills * 2, 20)  # Up to 20 bonus points
        else:
            # Default score if no comparison possible
            match_score = 60
            
        # Cap the score
        match_score = min(match_score, 100)
        
        # Format strengths and weaknesses
        strengths = matched_skills[:5] if matched_skills else ["Experience appears relevant to the position"]
        weaknesses = missing_skills[:3] if missing_skills else ["Unable to identify specific gaps without AI analysis"]
        
        return {
            "match_score": match_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "summary": f"Candidate {name} has a match score of {match_score}% based on keyword analysis. Full AI analysis unavailable."
        }
    
    def generate_interview_questions(self, job_description, candidate_data):
        """
        Generate tailored interview questions based on the job and candidate.
        
        Args:
            job_description: dict, parsed job description data
            candidate_data: dict, parsed candidate data
            
        Returns:
            list: Interview questions
        """
        # Extract relevant information
        position = job_description.get("position", "the position")
        requirements = job_description.get("requirements", [])
        
        strengths = candidate_data.get("strengths", [])
        weaknesses = candidate_data.get("weaknesses", [])
        
        # Format for the prompt
        formatted_requirements = "\n".join([f"- {req}" for req in requirements])
        formatted_strengths = "\n".join([f"- {strength}" for strength in strengths])
        formatted_weaknesses = "\n".join([f"- {weakness}" for weakness in weaknesses])
        
        prompt = f"""
        Generate 8-10 interview questions for a candidate applying for the position of {position}.
        
        Job Requirements:
        {formatted_requirements}
        
        Candidate Strengths:
        {formatted_strengths}
        
        Areas to Probe:
        {formatted_weaknesses}
        
        Create a mix of questions including:
        1. Technical questions related to the job requirements
        2. Behavioral questions to assess soft skills
        3. Questions to verify the candidate's strengths
        4. Questions to address potential gaps in experience
        
        Format your response as a JSON array of strings, with each string being a complete interview question.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse the response and extract questions
            questions_data = json.loads(response.choices[0].message.content)
            
            # Ensure we have a list of questions
            if isinstance(questions_data, list):
                questions = questions_data
            elif isinstance(questions_data, dict) and "questions" in questions_data:
                questions = questions_data["questions"]
            else:
                # Try to extract questions from any JSON structure
                questions = []
                for key, value in questions_data.items():
                    if isinstance(value, str):
                        questions.append(value)
                    elif isinstance(value, list):
                        questions.extend([item for item in value if isinstance(item, str)])
            
            logger.info(f"Generated {len(questions)} interview questions")
            
            return questions
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            # Generate fallback questions using job requirements
            fallback_questions = [
                "Tell me about your experience relevant to this position.",
                "What are your greatest strengths?",
                "What challenges have you faced in previous roles?",
                "How do you handle deadlines and pressure?",
                "What are your career goals?"
            ]
            
            # Add specific questions based on job requirements
            if requirements:
                for req in requirements[:3]:  # Use up to 3 requirements
                    fallback_questions.append(f"Can you describe your experience with {req}?")
                    
            # Add specific questions based on candidate strengths
            if strengths:
                strength = strengths[0] if strengths else "your technical skills"
                fallback_questions.append(f"You mentioned {strength}. Can you provide an example of how you've applied this in a previous role?")
                
            # Add specific questions based on weaknesses to address
            if weaknesses:
                weakness = weaknesses[0] if weaknesses else "certain areas"
                fallback_questions.append(f"How do you plan to develop your skills in {weakness}?")
                
            logger.info(f"Using fallback questions due to API error. Generated {len(fallback_questions)} questions.")
            return fallback_questions