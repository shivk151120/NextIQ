from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can log in now.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})
