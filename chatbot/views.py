import openai
from django.shortcuts import render

openai.api_key = "sk-05794cd4e3b6446bb87462d970c2d1cc"
openai.base_url = "https://api.deepseek.com"

def ask_question(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        code = request.POST.get('code')

        # Call DeepSeek API
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that helps debug code."},
                {"role": "user", "content": f"Question: {question}\n\nCode:\n{code}"}
            ],
            stream=False
        )

        result = response.choices[0].message.content
        return render(request, 'chatbot/response.html', {'response': result})

    return render(request, 'chatbot/form.html')
