from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Phrase, Like, Comment, Attempt, Badge
from django.contrib.auth import get_user_model
from .forms import PhraseForm
import json
import random

User = get_user_model()

# Motivational messages pool
MOTIVATION = [
    "Excellent! Keep it up!",
    "Great job! You're improving!",
    "Well done! Practice makes perfect!",
    "You're getting better every time!",
    "Keep trying! Success is near!"
]

@login_required
def home(request):
    if request.user.role in ['teacher', 'admin']:
        return teacher_dashboard(request)
    elif request.user.role == 'student':
        return student_dashboard(request)
    elif request.user.role == 'parent':
        return render(request, "core/parent_dashboard.html")
    else:
        return render(request, "core/dashboard.html")

# -----------------------------
@login_required
def teacher_dashboard(request):
    if request.user.role not in ['teacher', 'admin']:
        return redirect('home')

    phrases = Phrase.objects.all()
    students = User.objects.filter(role='student')

    student_data = []
    for student in students:
        attempts = Attempt.objects.filter(user=student)
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        points = correct_attempts  # 1 point per correct attempt
        badges = student.badges.all()  # use related_name from Badge model

        student_data.append({
            "student": student,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "points": points,
            "badges": badges
        })

    # Sort by points descending for leaderboard
    leaderboard = sorted(student_data, key=lambda x: x['points'], reverse=True)

    # All attempts for table
    attempts = Attempt.objects.all().order_by('-attempt_date')

    return render(request, "core/teacher_dashboard.html", {
        "phrases": phrases,
        "student_data": student_data,
        "leaderboard": leaderboard,
        "attempts": attempts
    })

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('home')

    phrases = Phrase.objects.all()
    attempts = Attempt.objects.filter(user=request.user).order_by('-attempt_date')
    badges = [b.name for b in request.user.badges.all()]
    total_points = attempts.filter(is_correct=True).count()

    return render(request, "core/student_dashboard.html", {
        "phrases": phrases,
        "attempts": attempts,
        "badges": badges,
        "total_points": total_points
    })

@login_required
def practice(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)

    if request.method == "POST":
        if 'comment_text' in request.POST:
            text = request.POST.get('comment_text')
            if text:
                Comment.objects.create(user=request.user, phrase=phrase, text=text)
                messages.success(request, "Comment added successfully!")
            return redirect('practice', phrase_id=phrase.id)
        elif 'like' in request.POST:
            existing_like = Like.objects.filter(user=request.user, phrase=phrase)
            if existing_like.exists():
                existing_like.delete()
            else:
                Like.objects.create(user=request.user, phrase=phrase)
            return redirect('practice', phrase_id=phrase.id)

    likes_count = Like.objects.filter(phrase=phrase).count()
    comments = Comment.objects.filter(phrase=phrase).order_by('-created_at')
    user_liked = Like.objects.filter(user=request.user, phrase=phrase).exists()
    user_attempts = Attempt.objects.filter(user=request.user, phrase=phrase).count()
    motivation = random.choice(MOTIVATION)

    return render(request, "core/practice.html", {
        "phrase": phrase,
        "likes_count": likes_count,
        "comments": comments,
        "user_liked": user_liked,
        "user_attempts": user_attempts,
        "motivation": motivation
    })

@login_required
def toggle_like(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)
    existing_like = Like.objects.filter(user=request.user, phrase=phrase)
    if existing_like.exists():
        existing_like.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, phrase=phrase)
        liked = True
    return JsonResponse({
        "liked": liked,
        "likes_count": Like.objects.filter(phrase=phrase).count()
    })

@login_required
def add_phrase(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    if request.method == 'POST':
        form = PhraseForm(request.POST, request.FILES)
        if form.is_valid():
            phrase = form.save(commit=False)
            phrase.created_by = request.user
            phrase.save()
            return redirect('home')
    else:
        form = PhraseForm()
    return render(request, 'core/add_phrase.html', {'form': form})

@login_required
def edit_phrase(request, phrase_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    phrase = get_object_or_404(Phrase, id=phrase_id)
    if request.method == 'POST':
        form = PhraseForm(request.POST, request.FILES, instance=phrase)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PhraseForm(instance=phrase)
    return render(request, 'core/edit_phrase.html', {'form': form, 'phrase': phrase})

@login_required
def delete_phrase(request, phrase_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    phrase = get_object_or_404(Phrase, id=phrase_id)
    phrase.delete()
    return redirect('home')

@login_required
def save_attempt(request, phrase_id):
    if request.method == "POST":
        data = json.loads(request.body)
        is_correct = data.get("is_correct", False)
        time_taken = data.get("time_taken", 0)
        phrase = get_object_or_404(Phrase, id=phrase_id)

        Attempt.objects.create(user=request.user, phrase=phrase, is_correct=is_correct, time_taken=time_taken)

        # Award badges
        total_correct = Attempt.objects.filter(user=request.user, is_correct=True).count()
        if total_correct == 5:
            Badge.objects.get_or_create(user=request.user, name="5 Correct Attempts")
        elif total_correct == 10:
            Badge.objects.get_or_create(user=request.user, name="10 Correct Attempts")

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "failed"}, status=400)
