import os

import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render

# Use OpenRouter API (better free tier)
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', "v1-8ff155357bfab619e1cca680b3790fc701724abb9de720e5ac4cf91672075cb3")

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_question(request):
    if request.method == 'POST':
        question = request.POST.get('question', '')
        uploaded_files = request.FILES.getlist('files')

        print(f"Received question: {question}")
        print(f"Received files: {len(uploaded_files)} files")
        print(f"Using API key: {OPENROUTER_API_KEY[:20]}...")

        # Process uploaded files
        file_contents = []
        if uploaded_files:
            for file in uploaded_files:
                try:
                    # Read file content
                    file_content = file.read().decode('utf-8', errors='ignore')
                    file_contents.append(f"File: {file.name}\nContent:\n{file_content}\n")
                    print(f"Processed file: {file.name} ({len(file_content)} characters)")
                except Exception as e:
                    print(f"Error processing file {file.name}: {str(e)}")
                    file_contents.append(f"File: {file.name}\nError: Could not read file content\n")

        # Combine question and file contents
        full_content = question
        if file_contents:
            full_content += "\n\n" + "\n".join(file_contents)

        print(f"Total content length: {len(full_content)} characters")

        # Prepare the messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert coding mentor that helps students understand and solve programming problems. Provide clear, step-by-step explanations and always include code examples when relevant. When analyzing uploaded files, provide detailed feedback on the code structure, potential improvements, and best practices."
            },
            {
                "role": "user",
                "content": full_content
            }
        ]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "LeetAI Coding Mentor"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 1500
        }

        try:
            print("Sending request to OpenRouter API...")
            print(f"URL: {OPENROUTER_API_URL}")
            print(f"Headers: {dict(headers)}")
            print(f"Payload keys: {list(payload.keys())}")
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                print("401 Unauthorized - API key issue")
                print(f"Response body: {response.text}")
                error_message = "API key authentication failed. Please check your OpenRouter API key."
                return render(request, 'chatbot/response.html', {'response': error_message})
            
            if response.status_code == 402:
                print("402 Payment Required - Quota exceeded")
                print(f"Response body: {response.text}")
                error_message = "API quota exceeded. Please check your OpenRouter account balance."
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
