# Google Reviews Sentiment Analyzer

This Streamlit application analyzes the sentiment of Google My Business reviews using ChatGPT. It identifies negative reviews and provides a summary of specific issues mentioned by customers.

## Features

- Fetch reviews from Google My Business API
- Analyze sentiment using ChatGPT
- Identify and summarize negative reviews
- Export results to CSV
- Customizable analysis prompt

## Setup Instructions

### Prerequisites

- Python 3.7+
- Google My Business API credentials
- OpenAI API key
- Google My Business Account ID and Location ID

### Installation

1. Clone this repository:
   ```bash
   git clone [your-repo-url]
   cd [your-repo-name]
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `credentials.json` file with your Google My Business API credentials:
   - Go to the Google Cloud Console
   - Create a service account and download the JSON credentials
   - Place the file in the root directory of the app

### Running the App

Run the Streamlit app with:
```bash
streamlit run app.py
```

### Configuration

In the app's sidebar, you'll need to provide:
1. Your OpenAI API key
2. Your Google My Business Account ID
3. Your Google My Business Location ID

## How It Works

1. The app connects to the Google My Business API and fetches reviews for the specified location
2. It then sends these reviews to ChatGPT along with your custom prompt
3. ChatGPT analyzes the sentiment and identifies negative reviews
4. The results are displayed in the app and can be downloaded as a CSV file

## Customizing the Analysis

You can customize the analysis prompt in the app to focus on specific aspects of the reviews or to change the output format.

## Finding Your Google My Business IDs

To find your Account ID and Location ID:
1. Log in to your Google My Business account
2. Navigate to the API Access section
3. Your Account ID will be displayed there
4. Select your location to view its ID

## Troubleshooting

- If you encounter issues with the Google API, ensure your credentials have the correct permissions
- If the sentiment analysis isn't working, check your OpenAI API key and quota
- For any other issues, check the error messages in the app or review the Streamlit logs

## License

[Your License Information]
