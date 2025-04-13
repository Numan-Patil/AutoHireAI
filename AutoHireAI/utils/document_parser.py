import re
import io
import logging
from PyPDF2 import PdfReader
from docx import Document
import nltk
from nltk.tokenize import sent_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Define custom sentence tokenizer function that doesn't rely on punkt_tab
def safe_sent_tokenize(text, language='english'):
    """
    A safer implementation of sent_tokenize that doesn't require punkt_tab resources.
    Falls back to simple regex splitting if punkt is not available.
    """
    try:
        return sent_tokenize(text)
    except LookupError:
        # Simple fallback: split by common sentence endings
        import re
        return re.split(r'(?<=[.!?])\s+', text)

class DocumentParser:
    """
    Class to handle parsing of different document formats like PDF and DOCX.
    """
    
    @staticmethod
    def extract_text_from_pdf(file_stream):
        """
        Extract text content from a PDF file.
        
        Args:
            file_stream: BytesIO object containing the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        try:
            pdf_reader = PdfReader(file_stream)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    @staticmethod
    def extract_text_from_docx(file_stream):
        """
        Extract text content from a DOCX file.
        
        Args:
            file_stream: BytesIO object containing the DOCX file
            
        Returns:
            str: Extracted text from the DOCX
        """
        try:
            doc = Document(file_stream)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    @staticmethod
    def extract_text(file_stream, filename):
        """
        Extract text from a file based on its extension.
        
        Args:
            file_stream: BytesIO object containing the file
            filename: Original filename with extension
            
        Returns:
            str: Extracted text from the file
        """
        # Create a BytesIO object to work with
        file_content = io.BytesIO(file_stream.read())
        
        # Determine file type from extension
        if filename.lower().endswith('.pdf'):
            return DocumentParser.extract_text_from_pdf(file_content)
        elif filename.lower().endswith(('.docx', '.doc')):
            return DocumentParser.extract_text_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    
    @staticmethod
    def extract_email(text):
        """
        Extract email address from text.
        
        Args:
            text: str, the text to search in
            
        Returns:
            str: First email found or None
        """
        # Email regex pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_name(text, max_lines=10):
        """
        Attempt to extract a name from the beginning of a document.
        This is a simple heuristic that looks for a name pattern in the first few lines.
        
        Args:
            text: str, the text to search in
            max_lines: int, maximum number of lines to check
            
        Returns:
            str: Extracted name or None
        """
        # Check the first few lines for a name
        lines = [line.strip() for line in text.split('\n') if line.strip()][:max_lines]
        
        # Look for common name patterns (1-3 words with uppercase first letters)
        name_pattern = r'^([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})$'
        
        for line in lines:
            match = re.match(name_pattern, line)
            if match:
                return match.group(0)
        
        # If no match found, try looking for "Name:" or similar patterns
        for line in lines:
            if ":" in line:
                label, value = line.split(":", 1)
                if label.lower().strip() in ["name", "full name"]:
                    return value.strip()
        
        return None
    
    @staticmethod
    def extract_education(text):
        """
        Extract education information from text.
        
        Args:
            text: str, the text to search in
            
        Returns:
            str: Description of highest education found
        """
        # Look for education keywords
        education_keywords = [
            "Ph.D.", "PhD", "Doctorate", 
            "Master", "MS ", "M.S.", "MSc", "M.Sc", "MA ", "M.A.", 
            "Bachelor", "BS ", "B.S.", "BA ", "B.A.", "BSc", "B.Sc",
            "Engineering", "Computer Science", "Information Technology",
            "University", "College"
        ]
        
        sentences = safe_sent_tokenize(text)
        
        # Search for sentences containing education keywords
        education_sentences = []
        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in education_keywords):
                education_sentences.append(sentence)
        
        if education_sentences:
            # Return the most relevant education sentence (using a simple heuristic)
            # Prioritize higher education levels
            for keyword in ["Ph.D.", "PhD", "Doctorate"]:
                for sentence in education_sentences:
                    if keyword.lower() in sentence.lower():
                        return sentence.strip()
            
            for keyword in ["Master", "MS ", "M.S.", "MSc", "M.Sc"]:
                for sentence in education_sentences:
                    if keyword.lower() in sentence.lower():
                        return sentence.strip()
            
            # If no higher degrees found, return the first education sentence
            return education_sentences[0].strip()
        
        return "No education information found"
    
    @staticmethod
    def extract_experience(text):
        """
        Extract years of experience from text.
        
        Args:
            text: str, the text to search in
            
        Returns:
            str: Description of experience
        """
        # Look for experience indicators
        experience_patterns = [
            r'(\d+)\s*(?:\+)?\s*years?\s*(?:of)?\s*experience',
            r'experience\s*(?:of|:)?\s*(\d+)\s*(?:\+)?\s*years?',
            r'worked\s*(?:for)?\s*(\d+)\s*(?:\+)?\s*years?'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years = match.group(1)
                return f"{years}+ years"
        
        # If no specific years found, check for sections titled "Experience"
        if "experience" in text.lower():
            # Just return a generic response
            return "Has relevant experience"
        
        return "Experience not specified"
    
    @staticmethod
    def extract_skills(text):
        """
        Extract technical skills from text.
        
        Args:
            text: str, the text to search in
            
        Returns:
            list: List of identified skills
        """
        # List of common technical skills to look for
        common_skills = [
            # Programming languages
            "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", "Swift", "Go", "Kotlin",
            "TypeScript", "R", "Rust", "Scala", "Perl", "HTML", "CSS", "SQL",
            
            # Frameworks & Libraries
            "React", "Angular", "Vue", "Django", "Flask", "Spring", "Node.js", "Express",
            "TensorFlow", "PyTorch", "Keras", "Pandas", "NumPy", "Scikit-learn",
            
            # Databases
            "MySQL", "PostgreSQL", "MongoDB", "Oracle", "SQL Server", "Firebase", "Redis",
            "Elasticsearch", "Cassandra", "DynamoDB", "GraphQL",
            
            # Cloud & DevOps
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "CI/CD",
            "Git", "GitHub", "GitLab", "Terraform", "Ansible", "Heroku", "Serverless",
            
            # Other technical skills
            "Machine Learning", "Artificial Intelligence", "Data Science", "Blockchain",
            "Cyber Security", "Network Security", "Data Analysis", "Big Data", "IoT",
            "Agile", "Scrum", "RESTful API", "Microservices", "Cloud Computing",
            "UI/UX", "Mobile Development", "Web Development", "Testing", "QA",
            
            # Soft skills
            "Leadership", "Communication", "Teamwork", "Problem Solving", "Time Management",
            "Critical Thinking", "Creativity", "Project Management"
        ]
        
        # Extract skills that appear in the text
        found_skills = []
        for skill in common_skills:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
        
        return found_skills