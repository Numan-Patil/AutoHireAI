import re
import nltk
import logging
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

# Download NLTK resources if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

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

class NLPProcessor:
    """
    Class to handle natural language processing tasks for text analysis.
    """
    
    @staticmethod
    def extract_key_phrases(text, top_n=10):
        """
        Extract key phrases from text.
        
        Args:
            text: str, the input text
            top_n: int, number of top phrases to return
            
        Returns:
            list: Top phrases found in the text
        """
        # Tokenize and clean text
        sentences = safe_sent_tokenize(text)
        stop_words = set(stopwords.words('english'))
        
        # Add common document words to stop words
        additional_stop_words = {
            "resume", "cv", "curriculum", "vitae", "page", "email", "contact", 
            "address", "phone", "tel", "reference", "references", "name", "date",
            "job", "position", "work", "experience", "education", "skill", "skills",
            "proficient", "proficiency", "knowledge", "understanding", "familiar",
            "expert", "expertise", "professional"
        }
        stop_words.update(additional_stop_words)
        
        # Extract phrases (2-3 words)
        phrases = []
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            words = [word for word in words if word.isalnum() and word not in stop_words]
            
            # Generate bigrams and trigrams
            for i in range(len(words) - 1):
                phrases.append(" ".join(words[i:i+2]))
            
            for i in range(len(words) - 2):
                phrases.append(" ".join(words[i:i+3]))
        
        # Count and return top phrases
        phrase_counts = Counter(phrases)
        top_phrases = [phrase for phrase, _ in phrase_counts.most_common(top_n)]
        
        return top_phrases
    
    @staticmethod
    def extract_keywords(text, top_n=20):
        """
        Extract key individual words from text.
        
        Args:
            text: str, the input text
            top_n: int, number of top keywords to return
            
        Returns:
            list: Top keywords found in the text
        """
        # Tokenize and clean text
        stop_words = set(stopwords.words('english'))
        
        # Add common document words to stop words
        additional_stop_words = {
            "resume", "cv", "curriculum", "vitae", "page", "email", "contact", 
            "address", "phone", "tel", "reference", "references", "name", "date"
        }
        stop_words.update(additional_stop_words)
        
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
        
        # Count and return top words
        word_counts = Counter(words)
        top_words = [word for word, _ in word_counts.most_common(top_n)]
        
        return top_words
    
    @staticmethod
    def summarize_text(text, num_sentences=5):
        """
        Create a simple extractive summary by selecting the most important sentences.
        
        Args:
            text: str, the input text
            num_sentences: int, number of sentences for the summary
            
        Returns:
            str: Summarized text
        """
        # Tokenize text into sentences and words
        sentences = safe_sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text  # Return original if it's already short
        
        stop_words = set(stopwords.words('english'))
        word_frequencies = {}
        
        # Calculate word frequencies
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            for word in words:
                if word.isalnum() and word not in stop_words:
                    if word not in word_frequencies:
                        word_frequencies[word] = 1
                    else:
                        word_frequencies[word] += 1
        
        # Normalize frequencies
        if word_frequencies:
            max_frequency = max(word_frequencies.values())
            for word in word_frequencies:
                word_frequencies[word] = word_frequencies[word] / max_frequency
        
        # Calculate sentence scores
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            words = word_tokenize(sentence.lower())
            score = 0
            for word in words:
                if word in word_frequencies:
                    score += word_frequencies[word]
            
            # Favor sentences at the beginning and end
            position_weight = 1.0
            if i < len(sentences) * 0.2:  # First 20% of document
                position_weight = 1.2
            elif i > len(sentences) * 0.8:  # Last 20% of document
                position_weight = 1.1
                
            sentence_scores[i] = score * position_weight
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        top_sentence_indices = sorted(top_sentence_indices)  # Sort by original order
        
        summary = " ".join([sentences[i] for i in top_sentence_indices])
        return summary
    
    @staticmethod
    def preprocess_text(text):
        """
        Clean and preprocess text for analysis.
        
        Args:
            text: str, the input text
            
        Returns:
            str: Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove unwanted characters and extra whitespace
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = text.strip()
        
        return text
    
    @staticmethod
    def calculate_similarity_score(jd_text, cv_text):
        """
        Calculate a simple similarity score between job description and CV.
        
        Args:
            jd_text: str, the job description text
            cv_text: str, the CV text
            
        Returns:
            float: Similarity score (0-100)
        """
        # Preprocess texts
        jd_processed = NLPProcessor.preprocess_text(jd_text)
        cv_processed = NLPProcessor.preprocess_text(cv_text)
        
        # Extract keywords from job description
        jd_keywords = set(NLPProcessor.extract_keywords(jd_processed, top_n=50))
        
        # Tokenize CV
        cv_words = set(word_tokenize(cv_processed))
        
        # Calculate overlap
        matching_words = jd_keywords.intersection(cv_words)
        
        if not jd_keywords:
            return 0
        
        # Calculate basic similarity score
        similarity = len(matching_words) / len(jd_keywords) * 100
        
        # Cap at 100
        similarity = min(similarity, 100)
        
        return similarity
    
    @staticmethod
    def extract_requirements(text):
        """
        Extract job requirements from job description text.
        
        Args:
            text: str, the job description text
            
        Returns:
            list: List of job requirements
        """
        # Look for requirements section
        text_lower = text.lower()
        req_keywords = ["requirements", "qualifications", "what you'll need", "what we're looking for", "required skills"]
        
        requirements = []
        
        # Find the requirements section
        req_section = None
        req_section_start = None
        
        for keyword in req_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Find the start of the section
                req_section_start = idx
                
                # Extract the section (limit to 1000 chars)
                section_end = min(idx + 1000, len(text))
                req_section = text[idx:section_end]
                break
        
        if req_section:
            # Look for bullet points or numbered lists
            lines = req_section.split('\n')
            for line in lines:
                line = line.strip()
                # Skip empty lines and the header line
                if not line or any(keyword in line.lower() for keyword in req_keywords):
                    continue
                
                # Check for bullet point patterns or numbered lists
                if re.match(r'^[\s•\-*]+', line) or re.match(r'^\d+\.', line):
                    # Clean up the line
                    clean_line = re.sub(r'^[\s•\-*\d\.]+', '', line).strip()
                    if clean_line and len(clean_line) > 10:  # Ensure it's substantial
                        requirements.append(clean_line)
                
                # If we already have a few requirements, stop processing
                if len(requirements) >= 8:
                    break
        
        # If no bullet points found, try extracting sentences with requirement keywords
        if not requirements:
            skill_keywords = [
                "experience", "knowledge", "proficiency", "expertise", "familiarity", 
                "skill", "ability", "competency", "understanding", "proficient"
            ]
            
            sentences = safe_sent_tokenize(text)
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in skill_keywords):
                    if 30 <= len(sentence) <= 150:  # Reasonable length for a requirement
                        requirements.append(sentence)
                
                if len(requirements) >= 8:
                    break
        
        # If still no requirements, just return a few top keywords
        if not requirements:
            keywords = NLPProcessor.extract_keywords(text, top_n=10)
            for keyword in keywords:
                requirements.append(f"Proficiency in {keyword}")
                if len(requirements) >= 5:
                    break
        
        return requirements[:8]  # Limit to 8 requirements
