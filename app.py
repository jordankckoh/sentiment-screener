import streamlit as st
import os
import json
import re
import pandas as pd
import openai
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Set page configuration
st.set_page_config(page_title="Review Sentiment Analyzer", layout="wide")

# Function to extract place ID from Google Maps URL
def extract_place_id(maps_url):
    # Pattern to match place_id in Google Maps URLs
    pattern = r"place/[^/]+/([^/]+)"
    # Alternative pattern for shorter URLs
    alt_pattern = r"maps\?.*?cid=(\d+)"
    
    # Try the first pattern
    match = re.search(pattern, maps_url)
    if match:
        return match.group(1)
    
    # Try the alternative pattern
    match = re.search(alt_pattern, maps_url)
    if match:
        return match.group(1)
    
    return None

# Function to load credentials from JSON
def load_google_credentials():
    if os.path.exists('credentials.json'):
        return Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/business.manage', 
                   'https://www.googleapis.com/auth/places']
        )
    else:
        st.error("Google API credentials file not found. Please add credentials.json to the app directory.")
        return None

# Function to get Google reviews from a Place ID
def get_google_reviews_by_place_id(place_id, credentials):
    try:
        # Build the Places API service
        service = build('places', 'v1', credentials=credentials)
        
        # Get place details including reviews
        place_details = service.places().get(
            name=f'places/{place_id}',
            fields='id,displayName,reviews'
        ).execute()
        
        # Extract reviews
        reviews = place_details.get('reviews', [])
        place_name = place_details.get('displayName', 'Unknown Location')
        
        return reviews, place_name
    
    except Exception as e:
        st.error(f"Error fetching reviews: {str(e)}")
        return [], "Unknown Location"

# Function to get Google reviews using Business API (fallback)
def get_google_reviews(account_id, location_id, credentials):
    try:
        # Build the My Business Information API
        mybusiness = build('mybusiness', 'v4', credentials=credentials)
        
        # Get reviews
        reviews = mybusiness.accounts().locations().reviews().list(
            parent=f'accounts/{account_id}/locations/{location_id}',
            pageSize=50
        ).execute()
        
        return reviews.get('reviews', [])
    
    except Exception as e:
        st.error(f"Error fetching reviews using Business API: {str(e)}")
        return []

# Function to analyze sentiment with ChatGPT
def analyze_sentiment(prompt, reviews, api_key, place_name=""):
    openai.api_key = api_key
    
    # Format reviews based on the API source (Places API vs Business API)
    if reviews and 'author' in reviews[0]:  # Places API format
        reviews_text = "\n\n".join([
            f"Reviewer: {review.get('author', {}).get('displayName', 'Anonymous')}\n"
            f"Rating: {review.get('rating', 'No rating')}/5\n"
            f"Comment: {review.get('text', {}).get('text', 'No comment')}"
            for review in reviews
        ])
    else:  # Business API format
        reviews_text = "\n\n".join([
            f"Reviewer: {review.get('reviewer', {}).get('displayName', 'Anonymous')}\n"
            f"Rating: {review.get('starRating', 'No rating')}\n"
            f"Comment: {review.get('comment', 'No comment')}"
            for review in reviews
        ])
    
    location_info = f"Business Name: {place_name}\n\n" if place_name else ""
    full_prompt = f"{prompt}\n\n{location_info}{reviews_text}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful review sentiment analyzer."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"Error analyzing sentiment: {str(e)}")
        return "Error analyzing sentiment. Please check your OpenAI API key and try again."

# Sidebar for configuration
st.sidebar.title("Configuration")

# OpenAI API Key
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# Main app
st.title("Google Review Sentiment Analyzer")

# Google Maps URL input
maps_url = st.text_input("Google Maps Location URL", 
                        placeholder="https://www.google.com/maps/place/...")

# Advanced options in expander
with st.expander("Advanced Options (Optional)"):
    use_direct_ids = st.checkbox("Use Account/Location IDs directly instead of Maps URL")
    
    if use_direct_ids:
        col1, col2 = st.columns(2)
        with col1:
            google_account_id = st.text_input("Google My Business Account ID")
        with col2:
            google_location_id = st.text_input("Google My Business Location ID")

# Prompt template
default_prompt = """Analyze the sentiment of the following Google reviews. 
Provide an overall sentiment score for all reviews combined (positive, neutral, or negative).
Then, identify any reviews with negative sentiment and list them with the following information:
1. Username of the reviewer
2. The full review text
3. A brief summary of the specific issues or complaints mentioned

Format your response as:
Overall Sentiment: [positive/neutral/negative]

Negative Reviews:
[Username]: [Review Text]
Issue Summary: [Brief summary of the problems mentioned]
"""

st.subheader("Analysis Prompt")
prompt = st.text_area("Customize how the AI should analyze the reviews", value=default_prompt, height=250)

# Main analysis button
if st.button("Analyze Reviews"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not maps_url and not (use_direct_ids and google_account_id and google_location_id):
        st.error("Please enter either a Google Maps URL or use the advanced options to provide Account/Location IDs.")
    else:
        with st.spinner("Loading credentials..."):
            credentials = load_google_credentials()
            
        if credentials:
            reviews = []
            place_name = ""
            
            # Determine which method to use to fetch reviews
            if use_direct_ids and google_account_id and google_location_id:
                with st.spinner("Fetching reviews using Account/Location IDs..."):
                    reviews = get_google_reviews(google_account_id, google_location_id, credentials)
            else:
                with st.spinner("Extracting place ID from Google Maps URL..."):
                    place_id = extract_place_id(maps_url)
                    
                if place_id:
                    with st.spinner(f"Fetching reviews for place ID: {place_id}..."):
                        reviews, place_name = get_google_reviews_by_place_id(place_id, credentials)
                else:
                    st.error("Could not extract place ID from the provided Google Maps URL. Please check the URL format.")
                
            if reviews:
                st.success(f"Successfully retrieved {len(reviews)} reviews for {place_name or 'the location'}.")
                
                # Display raw reviews in an expander
                with st.expander("View Raw Reviews"):
                    for i, review in enumerate(reviews):
                        st.markdown(f"### Review {i+1}")
                        
                        # Handle different API response formats
                        if 'author' in review:  # Places API format
                            st.markdown(f"**Reviewer:** {review.get('author', {}).get('displayName', 'Anonymous')}")
                            st.markdown(f"**Rating:** {review.get('rating', 'No rating')}/5")
                            st.markdown(f"**Comment:** {review.get('text', {}).get('text', 'No comment')}")
                        else:  # Business API format
                            st.markdown(f"**Reviewer:** {review.get('reviewer', {}).get('displayName', 'Anonymous')}")
                            st.markdown(f"**Rating:** {review.get('starRating', 'No rating')}")
                            st.markdown(f"**Comment:** {review.get('comment', 'No comment')}")
                            
                        st.markdown("---")
                
                # Analyze sentiment
                with st.spinner("Analyzing sentiment..."):
                    analysis = analyze_sentiment(prompt, reviews, openai_api_key, place_name)
                
                # Display results
                st.subheader("Sentiment Analysis Results")
                st.markdown(analysis)
                
                # Option to download results as CSV
                if st.button("Download Results as CSV"):
                    # Parse the analysis to create a DataFrame
                    lines = analysis.split('\n')
                    
                    # Extract overall sentiment
                    overall_sentiment = ""
                    for line in lines:
                        if "Overall Sentiment:" in line:
                            overall_sentiment = line.split("Overall Sentiment:")[1].strip()
                            break
                    
                    # Create a DataFrame for negative reviews
                    negative_reviews = []
                    current_user = ""
                    current_review = ""
                    current_summary = ""
                    
                    parsing_negative = False
                    for line in lines:
                        if "Negative Reviews:" in line:
                            parsing_negative = True
                            continue
                        
                        if parsing_negative:
                            if line.strip() == "":
                                continue
                            
                            if "Issue Summary:" in line:
                                current_summary = line.split("Issue Summary:")[1].strip()
                                negative_reviews.append({
                                    "Username": current_user,
                                    "Review": current_review,
                                    "Issue Summary": current_summary
                                })
                                current_user = ""
                                current_review = ""
                                current_summary = ""
                            elif ":" in line and not current_user:
                                parts = line.split(":", 1)
                                current_user = parts[0].strip()
                                current_review = parts[1].strip()
                    
                    # Create DataFrame and download
                    if negative_reviews:
                        df = pd.DataFrame(negative_reviews)
                        df['Business Name'] = place_name
                        df['Overall Sentiment'] = overall_sentiment
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"negative_reviews_{place_name.replace(' ', '_')}.csv",
                            mime="text/csv",
                        )
            else:
                st.warning("No reviews found for the specified location.")

# Add some helpful information at the bottom
st.markdown("---")
st.markdown("""
### How to use this app:
1. Enter your OpenAI API key in the sidebar
2. Paste a Google Maps URL for the business you want to analyze (e.g., https://www.google.com/maps/place/...)
3. Customize the analysis prompt if needed
4. Click "Analyze Reviews" to process the data
5. View the results and download as CSV if needed

For advanced users, you can directly use Google My Business Account and Location IDs instead of a Maps URL.
""")
