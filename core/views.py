from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from .models import (
    Phrase, Like, Comment, Attempt, User,
    BeltAward, belt_for_correct, Example, SiteSetting, ParentLink
)
from .forms import PhraseForm, ExampleForm, SiteSettingForm, ParentLinkForm

User = get_user_model()


# -----------------------------
# Home → role router
# -----------------------------
@login_required
def home(request):
    if request.user.role in ['teacher', 'admin']:
        return teacher_dashboard(request)
    elif request.user.role == 'student':
        return student_dashboard(request)
    elif request.user.role == 'parent':
        return parent_dashboard(request)
    return render(request, "core/dashboard.html")


# -----------------------------
# Leaderboard data (JSON)
# -----------------------------
@login_required
def leaderboard_data(_request):
    qs = (
        Attempt.objects.filter(is_correct=True)
        .values("user__username")
        .annotate(points=Count("id"))
        .order_by("-points", "user__username")
    )
    data = []
    for row in qs:
        points = row["points"]
        belt = belt_for_correct(points)
        data.append({
            "username": row["user__username"],
            "points": points,
            "belt": belt,
        })
    return JsonResponse({"results": data})


# -----------------------------
# Teacher Dashboard
# -----------------------------
@login_required
def teacher_dashboard(request):
    if request.user.role not in ['teacher', 'admin']:
        return redirect('home')

    phrases = Phrase.objects.all().order_by("id")
    attempts = Attempt.objects.select_related("user", "phrase").order_by('-attempt_date')

    top = (
        Attempt.objects.filter(is_correct=True)
        .values("user__username")
        .annotate(points=Count("id"))
        .order_by("-points", "user__username")[:10]
    )

    link_form = ParentLinkForm()
    existing_links = ParentLink.objects.select_related("student", "parent").all()

    site_settings = SiteSetting.get()
    site_form = SiteSettingForm(instance=site_settings) if request.user.role == 'admin' else None

    return render(request, "core/teacher_dashboard.html", {
        "phrases": phrases,
        "attempts": attempts,
        "leader_preview": top,
        "link_form": link_form,
        "existing_links": existing_links,
        "site_form": site_form,
    })


# -----------------------------
# Student Dashboard
# -----------------------------
@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('home')

    phrases = Phrase.objects.all().order_by("id")
    attempts = Attempt.objects.filter(user=request.user).select_related("phrase").order_by('-attempt_date')
    total_points = attempts.filter(is_correct=True).count()
    current_belt = belt_for_correct(total_points)

    return render(request, "core/student_dashboard.html", {
        "phrases": phrases,
        "attempts": attempts,
        "total_points": total_points,
        "current_belt": current_belt,
    })


# -----------------------------
# Parent Dashboard
# -----------------------------
@login_required
def parent_dashboard(request):
    if request.user.role != 'parent':
        return redirect('home')

    students = User.objects.filter(linked_parents__parent=request.user).distinct()
    data = []
    for s in students:
        attempts = Attempt.objects.filter(user=s).count()
        correct = Attempt.objects.filter(user=s, is_correct=True).count()
        data.append({
            "student": s,
            "total": attempts,
            "correct": correct,
            "belt": belt_for_correct(correct),
        })

    return render(request, "core/parent_dashboard.html", {"children": data})


# -----------------------------
# Practice page
# -----------------------------
@login_required
def practice(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)

    if request.method == "POST":
        if 'comment_text' in request.POST:
            txt = request.POST.get('comment_text', '').strip()
            if txt:
                Comment.objects.create(user=request.user, phrase=phrase, text=txt)
                messages.success(request, "Comment added!")
            return redirect('practice', phrase_id=phrase.id)
        elif 'like' in request.POST:
            like_qs = Like.objects.filter(user=request.user, phrase=phrase)
            if like_qs.exists():
                like_qs.delete()
            else:
                Like.objects.create(user=request.user, phrase=phrase)
            return redirect('practice', phrase_id=phrase.id)

    likes_count = Like.objects.filter(phrase=phrase).count()
    comments = Comment.objects.filter(phrase=phrase).order_by('-created_at')
    user_liked = Like.objects.filter(user=request.user, phrase=phrase).exists()
    user_attempts = Attempt.objects.filter(user=request.user, phrase=phrase).count()

    return render(request, "core/practice.html", {
        "phrase": phrase,
        "likes_count": likes_count,
        "comments": comments,
        "user_liked": user_liked,
        "user_attempts": user_attempts,
        "now": timezone.now(),
    })


# -----------------------------
# Save attempt + award belts
# -----------------------------
@login_required
@require_POST
def save_attempt(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)
    data = json.loads(request.body.decode("utf-8"))
    is_correct = bool(data.get("is_correct", False))
    time_taken = int(data.get("time_taken", 0))

    Attempt.objects.create(
        user=request.user, phrase=phrase, is_correct=is_correct, time_taken=time_taken
    )

    total_correct = Attempt.objects.filter(user=request.user, is_correct=True).count()
    current_belt = belt_for_correct(total_correct)

    if not BeltAward.objects.filter(user=request.user, name=current_belt).exists():
        BeltAward.objects.create(user=request.user, name=current_belt)

    return JsonResponse({
        "ok": True,
        "total_correct": total_correct,
        "belt": current_belt,
        "points": total_correct
    })


# -----------------------------
# Phrase CRUD
# -----------------------------
@login_required
def add_phrase(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    if request.method == 'POST':
        form = PhraseForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.created_by = request.user
            p.save()
            messages.success(request, "Phrase added.")
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
            messages.success(request, "Phrase updated.")
            return redirect('home')
    else:
        form = PhraseForm(instance=phrase)
    return render(request, 'core/edit_phrase.html', {'form': form, 'phrase': phrase})


@login_required
def delete_phrase(request, phrase_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    get_object_or_404(Phrase, id=phrase_id).delete()
    messages.success(request, "Phrase deleted.")
    return redirect('home')


# -----------------------------
# Admin: Site settings update
# -----------------------------
@login_required
def update_site_settings(request):
    if request.user.role != 'admin':
        return redirect('home')
    settings_obj = SiteSetting.get()
    if request.method == "POST":
        form = SiteSettingForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings saved.")
            return redirect('home')
    return redirect('home')


# -----------------------------
# Parent linking
# -----------------------------
@login_required
def add_parent_link(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    if request.method == "POST":
        form = ParentLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Parent linked to student.")
    return redirect('home')


@login_required
def delete_parent_link(request, link_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    ParentLink.objects.filter(id=link_id).delete()
    messages.success(request, "Link removed.")
    return redirect('home')


# -----------------------------
# Examples hub
# -----------------------------
@login_required
def examples_list(_request):
    items = Example.objects.all().order_by("-id")
    return render(_request, "core/examples_list.html", {"items": items})


@login_required
def example_detail(_request, example_id):
    item = get_object_or_404(Example, id=example_id)
    return render(_request, "core/example_detail.html", {"item": item})


# -----------------------------
# Static pages
# -----------------------------
@login_required
def about_page(request):
    return render(request, "core/about.html")


@login_required
def contact_page(request):
    return render(request, "core/contact.html")


@login_required
def examples_page(request):
    return render(request, "core/examples.html")


# -----------------------------
# Link student → parent
# -----------------------------
@login_required
def link_student_parent(request):
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        parent_id = request.POST.get('parent_id')
        try:
            student = User.objects.get(id=student_id, role='student')
            parent = User.objects.get(id=parent_id, role='parent')
            student.parent = parent
            student.save()
            messages.success(request, f"Linked {student.username} to {parent.username}.")
            return redirect('manage_links')
        except User.DoesNotExist:
            messages.error(request, "Invalid student or parent.")

    students = User.objects.filter(role='student')
    parents = User.objects.filter(role='parent')
    return render(request, 'core/link_student_parent.html', {'students': students, 'parents': parents})


@login_required
def manage_links(request):
    linked_students = User.objects.filter(role='student', parent__isnull=False)
    return render(request, 'core/manage_links.html', {'linked_students': linked_students})


# -----------------------------
# Leaderboard
# -----------------------------
@login_required
def leaderboard(request):
    students = User.objects.filter(role='student').annotate(
        total_correct=Count('attempts', filter=Q(attempts__is_correct=True))
    ).order_by('-total_correct', 'username')
    return render(request, 'core/leaderboard.html', {'students': students})


@login_required
def progress_graph(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    if request.user.role not in ['teacher', 'admin'] and request.user != student:
        return redirect('home')

    attempts = Attempt.objects.filter(user=student).order_by('attempt_date')
    graph_data = []
    correct_count = 0
    for att in attempts:
        if att.is_correct:
            correct_count += 1
        graph_data.append({
            "date": att.attempt_date.strftime("%Y-%m-%d %H:%M"),
            "correct": att.is_correct,
            "total_correct": correct_count,
            "belt": belt_for_correct(correct_count),
        })

    return render(request, 'core/progress_graph.html', {
        'student': student,
        'graph_data': graph_data,
    })
