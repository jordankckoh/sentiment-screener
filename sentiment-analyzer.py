import openai
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Class to handle sentiment analysis of reviews using ChatGPT"""
    
    def __init__(self, api_key):
        """
        Initialize the analyzer with an OpenAI API key
        
        Args:
            api_key (str): OpenAI API key
        """
        self.api_key = api_key
        openai.api_key = api_key
    
    def analyze(self, prompt, reviews, business_info=None):
        """
        Analyze sentiment of reviews using ChatGPT
        
        Args:
            prompt (str): The analysis prompt to use
            reviews (list): List of review data
            business_info (dict, optional): Additional business information
            
        Returns:
            dict: Analysis results with raw response and structured data
        """
        try:
            # Format the reviews for analysis
            formatted_reviews = self._format_reviews(reviews)
            
            # Prepare business context if available
            business_context = ""
            if business_info:
                business_context = f"Business Name: {business_info.get('name', 'Unknown')}\n"
                if 'formatted_address' in business_info:
                    business_context += f"Address: {business_info.get('formatted_address')}\n"
                if 'rating' in business_info:
                    business_context += f"Overall Rating: {business_info.get('rating')}/5\n"
                business_context += "\n"
            
            # Build the complete prompt
            full_prompt = f"{prompt}\n\n{business_context}{formatted_reviews}"
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful review sentiment analyzer."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Extract the response text
            analysis_text = response.choices[0].message['content']
            
            # Try to structure the data
            structured_data = self._structure_analysis(analysis_text)
            
            return {
                "success": True,
                "raw_analysis": analysis_text,
                "structured_data": structured_data
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_reviews(self, reviews):
        """
        Format reviews for analysis
        
        Args:
            reviews (list): List of review data
            
        Returns:
            str: Formatted reviews text
        """
        formatted = []
        
        for i, review in enumerate(reviews):
            # Handle different possible formats of review data
            if 'author' in review:  # Places API format
                reviewer = review.get('author', {}).get('displayName', 'Anonymous')
                rating = review.get('rating', 'No rating')
                comment = review.get('text', {}).get('text', 'No comment')
            else:  # Business API format
                reviewer = review.get('reviewer', {}).get('displayName', 'Anonymous')
                rating = review.get('starRating', 'No rating')
                comment = review.get('comment', 'No comment')
            
            # Build the formatted review text
            review_text = f"Review #{i+1}\n"
            review_text += f"Reviewer: {reviewer}\n"
            review_text += f"Rating: {rating}/5\n"
            review_text += f"Comment: {comment}\n"
            
            formatted.append(review_text)
        
        return "\n\n".join(formatted)
    
    def _structure_analysis(self, analysis_text):
        """
        Attempt to structure the analysis results
        
        Args:
            analysis_text (str): Raw analysis text from ChatGPT
            
        Returns:
            dict: Structured analysis data
        """
        try:
            # Extract overall sentiment
            overall_sentiment = None
            for line in analysis_text.split('\n'):
                if "Overall Sentiment:" in line:
                    overall_sentiment = line.split("Overall Sentiment:")[1].strip()
                    break
            
            # Extract negative reviews
            negative_reviews = []
            
            # State tracking
            in_negative_section = False
            current_review = {}
            
            for line in analysis_text.split('\n'):
                line = line.strip()
                
                # Start of negative reviews section
                if "Negative Reviews:" in line:
                    in_negative_section = True
                    continue
                
                if not in_negative_section or not line:
                    continue
                
                # Issue summary line
                if line.startswith("Issue Summary:"):
                    if current_review:
                        current_review["issue_summary"] = line[len("Issue Summary:"):].strip()
                        negative_reviews.append(current_review)
                        current_review = {}
                
                # Username and review text line
                elif ":" in line and not current_review:
                    parts = line.split(":", 1)
                    username = parts[0].strip()
                    review_text = parts[1].strip() if len(parts) > 1 else ""
                    
                    current_review = {
                        "username": username,
                        "review_text": review_text
                    }
            
            # Add the last review if there's one being processed
            if current_review and "issue_summary" in current_review:
                negative_reviews.append(current_review)
            
            return {
                "overall_sentiment": overall_sentiment,
                "negative_reviews": negative_reviews,
                "negative_count": len(negative_reviews)
            }
            
        except Exception as e:
            logger.warning(f"Failed to structure analysis: {str(e)}")
            return {
                "error": "Could not structure the analysis results"
            }
