from flask import Flask, request, render_template, jsonify, session
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from flask_cors import CORS
import re
from datetime import datetime
from io import BytesIO
import base64
from config import GOOGLE_API_KEY
import google.generativeai as genai
import uuid
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex (16)
CORS(app, supports_credentials=True)

genai.configure(api_key=GOOGLE_API_KEY)
summarizer = pipeline('summarization')
qa_model = pipeline('question-answering')
model = genai.GenerativeModel('gemini-pro')

@app.route('/start_session', methods=['POST'])
def start_session():
    session['user_id'] = str(uuid.uuid4())
    session['conversation_history'] = []
    return jsonify({'message': 'Session started'}), 200

def scrape_govtrack(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        bill_title = soup.find('h1').text.strip()
        bill_text_content = soup.find('div', id='main_text_content')
        if bill_text_content:
            texts = bill_text_content.find_all(text=True)
            visible_texts = [text.strip() for text in texts if text.parent.name not in ['style', 'script', '[document]', 'head', 'title']]
            full_text = '\n'.join(filter(bool, visible_texts))
        else:
            full_text = "Full text not available"
        
        return {
            'title': bill_title,
            'full_text': full_text,
        }
    except Exception as e:
        print(f"Error scraping data: {e}")
        return None

def generate_summary(text):
    prompt = f"""Please provide a concise summary of the following legislative bill:

    {text}

    Summarize the key points and main objectives of the bill in about 3-5 sentences."""

    response = model.generate_content(prompt)
    return response.text


def fetch_vote_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    vote_data = {}
    
    # Find the vote breakdown section
    vote_breakdown = soup.find('div', class_='vote-breakdown')
    if vote_breakdown:
        for vote_type in ['yes', 'no', 'not-voting']:
            vote_count = vote_breakdown.find('div', class_=f'vote-{vote_type}')
            if vote_count:
                count = vote_count.find('span', class_='count').text
                vote_data[vote_type.capitalize()] = int(count)
    
    return vote_data

def fetch_timeline_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    timeline_data = []
    
    # Find the bill status timeline section
    timeline = soup.find('ol', class_='bill_status_timeline')
    if timeline:
        for item in timeline.find_all('li'):
            date_str = item.find('span', class_='date').text.strip()
            event = item.find('span', class_='text').text.strip()
            date = datetime.strptime(date_str, '%b %d, %Y').strftime('%Y-%m-%d')
            timeline_data.append({
                "Event": event,
                "Start": date,
                "End": date
            })
    
    return timeline_data

def create_vote_visualization(vote_data):
    labels = list(vote_data.keys())
    sizes = list(vote_data.values())
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Vote Visualization')
    
    # Save to a BytesIO object
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()  # Close the plot to free up memory
    
    return f"data:image/png;base64,{img_str}"


def create_timeline(events):
    df = pd.DataFrame(events)
    fig = px.timeline(df, x_start="Start", x_end="End", y="Event")
    fig.write_image('static/timeline.png')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    url = request.json['url']
    data = scrape_govtrack(url)
    if data is None:
        return jsonify({'error': 'Failed to scrape data from the provided URL'}), 400
    
    summary = generate_summary(data['full_text'])
    
    return jsonify({
        'title': data['title'],
        'summary': summary,
        'full_text': data['full_text']
    })

@app.route('/ask', methods=['POST'])
def ask():
    try:
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            session['conversation_history'] = []

        question = request.json['question']
        context = request.json['context']
        
        conversation_history = session.get('conversation_history', [])
        conversation_history.append(f"Human: {question}")
        
        prompt = f"""You are an AI assistant specializing in explaining legislation and general political topics. Your primary source of information is the provided bill text, but you can also draw on your broader knowledge to provide context or explanations when necessary. Please respond to the following question about a bill or related topics.

Context (Bill Text):
{context}

Conversation History:
{' '.join(conversation_history[-5:])}

Please answer the following question:
{question}

Guidelines for your response:
1. If the answer is directly available in the bill text, use that information primarily.
2. If the question is related to the bill but not directly answered in the text, you may provide an answer based on your general knowledge, clearly stating that this information is not from the bill itself.
3. If the question is about politics or legislation in general, even if not directly related to the bill, you may answer using your broader knowledge.
4. Always be polite, informative, and as comprehensive as possible.
5. If you're unsure or the information isn't available, say so honestly.
6. Try to relate your answer back to the bill or its context whenever possible.

Provide a detailed and courteous response."""

        response = model.generate_content(prompt)
        answer = response.text

        conversation_history.append(f"AI: {answer}")
        session['conversation_history'] = conversation_history

        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error in ask route: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500



if __name__ == '__main__':
    app.run(debug=True)

