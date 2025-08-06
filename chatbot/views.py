import os

import requests
from django.shortcuts import render

# Use OpenRouter API (better free tier)
OPENROUTER_API_KEY = "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"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_question(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        code = request.POST.get('code')

        print(f"Received question: {question}")
        print(f"Received code: {code[:50] if code else 'None'}...")
        print(f"Using API key: {OPENROUTER_API_KEY[:10]}...")

        # Prepare the messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert coding mentor that helps students understand and solve programming problems. Provide clear, step-by-step explanations and always include code examples when relevant."
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nCode:\n{code}"
            }
        ]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "LeetAI Coding Mentor"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",  # Using GPT-3.5-turbo through OpenRouter
            "messages": messages,
            "max_tokens": 1000
        }

        try:
            print("Sending request to OpenRouter API...")
            print(f"URL: {OPENROUTER_API_URL}")
            print(f"Headers: {headers}")
            print(f"Payload: {payload}")
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                print("401 Unauthorized - API key issue")
                print(f"Response body: {response.text}")
                error_message = "API key authentication failed. Please check your OpenRouter API key."
                return render(request, 'chatbot/response.html', {'response': error_message})
            
            response.raise_for_status()
            result = response.json()['choices'][0]['message']['content']
            print(f"Response received: {len(result)} characters")
            return render(request, 'chatbot/response.html', {'response': result})

        except requests.exceptions.RequestException as e:
            print(f"OpenRouter API Error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response: {e.response.text}")
            error_message = f"Sorry, I encountered an error while processing your request. Please try again. Error: {str(e)}"
            return render(request, 'chatbot/response.html', {'response': error_message})

    return render(request, 'chatbot/form.html')
