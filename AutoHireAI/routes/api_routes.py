import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from utils.document_parser import DocumentParser
from utils.ai_analyzer import AIAnalyzer
from utils.email_utils import send_interview_invitation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
api_bp = Blueprint('api', __name__)

# Initialize AI analyzer
ai_analyzer = AIAnalyzer()

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
# Define allowed extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/')
def index():
    """API root endpoint"""
    return jsonify({"message": "Recruitment Assistant API", "status": "active"}), 200

@api_bp.route('/test-interview', methods=['POST'])
def test_interview():
    """Test endpoint for scheduling interviews with minimal data"""
    try:
        data = request.get_json()
        
        # Get candidate info from request or use default
        candidate = data.get('candidate', {})
        name = candidate.get('name', 'Test Candidate')
        email = candidate.get('email', 'test@example.com')
        
        # Create test request data
        test_data = {
            "candidates": [{
                "name": name,
                "email": email,
                "skills": ["Python", "JavaScript"],
                "experience": ["Software Developer"],
                "education": ["Bachelor's in Computer Science"]
            }],
            "interview_details": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "time": "10:00 AM",
                "mode": "virtual",
                "meeting_link": "https://zoom.us/j/123456789"
            },
            "job_description": {
                "position": "Software Engineer",
                "company_info": "Tech Company",
                "requirements": ["Python", "Web Development"]
            }
        }
        
        # Set the request context
        with api_bp.test_request_context(json=test_data):
            return schedule_interviews()
        
    except Exception as e:
        return jsonify({
            "message": "Error in test interview",
            "error": str(e)
        }), 500

@api_bp.route('/process-job-description', methods=['POST'])
def process_job_description():
    """
    Process uploaded job description file
    """
    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"message": "File type not supported. Please upload PDF or Word documents."}), 400
        
    try:
        # Extract text from file
        text = DocumentParser.extract_text(file, file.filename)
        
        if not text or len(text.strip()) < 50:
            return jsonify({"message": "Extracted text is too short or empty. Please check if the file contains readable text."}), 400
            
        # Process job description with AI
        jd_data = ai_analyzer.analyze_job_description(text)
        
        # Save uploaded file if needed
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.seek(0)  # Reset file pointer to beginning
        file.save(file_path)
        
        return jsonify(jd_data), 200
        
    except Exception as e:
        logger.error(f"Error processing job description: {str(e)}")
        return jsonify({"message": f"Error processing job description: {str(e)}"}), 500

@api_bp.route('/process-cv', methods=['POST'])
def process_cv():
    """
    Process uploaded CV file and match against job description
    """
    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"message": "File type not supported. Please upload PDF or Word documents."}), 400
        
    if 'job_description' not in request.form:
        return jsonify({"message": "Job description data is required"}), 400
        
    try:
        # Parse job description data
        job_description = json.loads(request.form['job_description'])
        
        # Extract text from file
        text = DocumentParser.extract_text(file, file.filename)
        
        if not text or len(text.strip()) < 50:
            return jsonify({"message": "Extracted text is too short or empty. Please check if the file contains readable text."}), 400
            
        # Extract basic info
        email = DocumentParser.extract_email(text)
        name = DocumentParser.extract_name(text)
        education = DocumentParser.extract_education(text)
        experience = DocumentParser.extract_experience(text)
        skills = DocumentParser.extract_skills(text)
        
        # Process CV with AI against job description
        cv_analysis = ai_analyzer.analyze_cv(text, job_description)
        
        # Combine all data
        result = {
            "name": name,
            "email": email,
            "education": education,
            "experience": experience,
            "skills": skills,
            "score": cv_analysis.get("match_score", 0),
            "strengths": cv_analysis.get("strengths", []),
            "weaknesses": cv_analysis.get("weaknesses", [])
        }
        
        # Save uploaded file if needed
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.seek(0)  # Reset file pointer to beginning
        file.save(file_path)
        
        return jsonify(result), 200
        
    except json.JSONDecodeError:
        logger.error("Invalid job description JSON data")
        return jsonify({"message": "Invalid job description data format"}), 400
    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}")
        return jsonify({"message": f"Error processing CV: {str(e)}"}), 500

@api_bp.route('/schedule-interviews', methods=['POST'])
def schedule_interviews():
    """
    Handle interview scheduling requests
    """
    if not request.json:
        return jsonify({"message": "Invalid data format. JSON required."}), 400
        
    try:
        data = request.json
        
        # Get current date for default value
        current_date = datetime.now().strftime('%Y-%m-%d')
        default_time = '10:00 AM'
        
        # Extract and normalize interview details from various possible field names
        interview_details = (
            data.get('interviewDetails') or 
            data.get('interview_details') or 
            data.get('InterviewDetails') or 
            data.get('interview') or 
            {}
        )
        
        # Extract date and time with defaults
        interview_date = (
            interview_details.get('date') or 
            data.get('interview_date') or 
            data.get('interviewDate') or
            current_date  # Default to today if not specified
        )
        interview_time = (
            interview_details.get('time') or 
            data.get('interview_time') or 
            data.get('interviewTime') or
            default_time  # Default to 10 AM if not specified
        )
        interview_mode = (
            interview_details.get('mode') or 
            data.get('interview_mode') or 
            data.get('interviewMode') or 
            'virtual'  # Default to virtual if not specified
        )
        
        # Update interview_details with normalized values
        interview_details = {
            'date': interview_date,
            'time': interview_time,
            'mode': interview_mode
        }
        
        # Extract candidates data
        candidates = data.get('candidates') or data.get('Candidates', [])
        
        # Extract or create job description
        job_description = (
            data.get('job_description') or 
            data.get('jobDescription') or 
            data.get('JobDescription') or
            {
                "position": "Open Position",
                "company_info": "Our Company",
                "requirements": ["Required skills and qualifications"]
            }
        )
        
        # Validate candidates
        if not candidates:
            return jsonify({"message": "Missing or empty 'candidates' field"}), 400
            
        # Validate date format
        try:
            interview_date_obj = datetime.strptime(interview_date, '%Y-%m-%d')
            # Ensure interview is not in the past
            if interview_date_obj.date() < datetime.now().date():
                interview_date = current_date
        except ValueError:
            # If invalid date, use current date
            logger.warning(f"Invalid date format received: {interview_date}, using current date")
            interview_date = current_date
        
        # Validate candidates array
        if not candidates or not isinstance(candidates, list):
            return jsonify({"message": "No candidates provided or invalid format"}), 400
            
        # Validate interview details
        required_interview_fields = ['date', 'time', 'mode']
        if not all(field in interview_details for field in required_interview_fields):
            return jsonify({"message": f"Interview details must include: {', '.join(required_interview_fields)}"}), 400
            
        # Validate job description
        if not job_description.get('position'):
            return jsonify({"message": "Job position is required in job description"}), 400
            
        # Process each candidate
        scheduled_candidates = []
        email_previews = []
        
        for candidate in candidates:
            # Validate candidate data
            if not isinstance(candidate, dict):
                logger.warning("Invalid candidate data format")
                continue
                
            # Extract candidate info
            candidate_name = candidate.get('name')
            candidate_email = candidate.get('email')
            
            # Skip if missing required info
            if not candidate_name or not candidate_email:
                logger.warning(f"Skipping candidate due to missing name or email: {candidate}")
                continue
            
            try:
                # Generate interview questions
                interview_questions = []
                candidate_data = {
                    "name": candidate_name,
                    "email": candidate_email,
                    "skills": candidate.get('skills', []),
                    "experience": candidate.get('experience', []),
                    "education": candidate.get('education', []),
                    "strengths": candidate.get('strengths', []),
                    "weaknesses": candidate.get('weaknesses', [])
                }
                
                try:
                    interview_questions = ai_analyzer.generate_interview_questions(
                        job_description,
                        candidate_data
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate interview questions: {str(e)}")
                    interview_questions = [
                        f"Can you tell us about your experience in {job_description['position']}?",
                        "What makes you a good fit for this position?",
                        "How do you handle challenges in the workplace?",
                        "What are your career goals and how does this position align with them?",
                        "Do you have any questions about the role or company?"
                    ]
                
                # Prepare location based on interview mode
                location = None
                mode = interview_details['mode'].lower()
                
                if mode == 'virtual':
                    location = interview_details.get('meeting_link')
                elif mode == 'in-person':
                    location = interview_details.get('office_address')
                
                # Log the email attempt
                logger.info(f"Sending interview invitation to {candidate_name} ({candidate_email})")
                
                # Send the interview invitation
                result = send_interview_invitation(
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    position=job_description['position'],
                    interview_date=interview_details['date'],
                    interview_time=interview_details['time'],
                    interview_mode=mode,
                    interview_location=location
                )
                
                if result['success']:
                    scheduled_candidates.append({
                        'name': candidate_name,
                        'email': candidate_email,
                        'questions': interview_questions,
                        'details': result['preview']
                    })
                    email_previews.append(result['preview'])
                    logger.info(f"Successfully scheduled interview for {candidate_name}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"Failed to send email to {candidate_name}: {error_msg}")
                    email_previews.append({
                        'name': candidate_name,
                        'email': candidate_email,
                        'error': error_msg
                    })
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing candidate {candidate_name}: {error_msg}")
                email_previews.append({
                    'name': candidate_name,
                    'email': candidate_email,
                    'error': error_msg
                })
        
        # Return results
        if not scheduled_candidates:
            return jsonify({
                "message": "No interviews were scheduled",
                "reason": "No valid candidates found or all email sends failed",
                "email_previews": email_previews
            }), 400
        
        return jsonify({
            "message": "Interviews scheduled successfully",
            "scheduled": len(scheduled_candidates),
            "candidates": scheduled_candidates,
            "email_previews": email_previews
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error scheduling interviews: {error_msg}")
        return jsonify({"message": "Error scheduling interviews", "error": error_msg}), 500