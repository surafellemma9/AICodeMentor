from django.shortcuts import render

# Create your views here.


def ask_question(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        code = request.POST.get('code')
        response = f"Question: {question}\n\nCode:\n{code}"
        return render(request, 'chatbot/response.html', {'response': response})
    
    return render(request, 'chatbot/form.html')