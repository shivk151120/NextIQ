from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SiteSetting
from .forms import SiteSettingForm

from .forms import ExampleForm

from .models import (
    Phrase, Like, Comment, Attempt, User, Lesson,
    BeltAward, belt_for_correct, Example, SiteSetting, ParentLink
)
from .forms import PhraseForm, LessonForm, ExampleForm, SiteSettingForm, ParentLinkForm
from django.contrib.auth.forms import UserCreationForm
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

    # All phrases
    phrases = Phrase.objects.all().order_by("id")

    # All attempts
    attempts = Attempt.objects.select_related("user", "phrase").order_by('-attempt_date')

    # Leaderboard preview
    top = (
        Attempt.objects.filter(is_correct=True)
        .values("user__username")
        .annotate(points=Count("id"))
        .order_by("-points", "user__username")[:10]
    )

    # Parent-Student links fetched dynamically
    existing_links = User.objects.filter(role='student', parent__isnull=False).select_related('parent')

    # Site settings
    site_settings = SiteSetting.get()
    site_form = SiteSettingForm(instance=site_settings) if request.user.role == 'admin' else None

    return render(request, "core/teacher_dashboard.html", {
        "phrases": phrases,
        "attempts": attempts,
        "leader_preview": top,
        "existing_links": existing_links,
        "site_form": site_form,
    })

# -----------------------------
# Student Dashboard
@login_required
def student_dashboard(request):
    # Ensure only students can access
    if request.user.role != 'student':
        return redirect('home')

    # Fetch phrases
    phrases = Phrase.objects.all().order_by("id")

    # Fetch attempts of this student with related phrase to optimize queries
    attempts = Attempt.objects.filter(user=request.user).select_related("phrase").order_by('-attempt_date')

    # Calculate total points (correct attempts)
    total_points = attempts.filter(is_correct=True).count()

    # Determine current belt based on points
    current_belt = belt_for_correct(total_points)

    # Fetch lessons for dashboard
    lessons = Lesson.objects.all().order_by("id")

    # Render dashboard with all required context
    return render(request, "core/student_dashboard.html", {
        "phrases": phrases,
        "attempts": attempts,
        "total_points": total_points,
        "current_belt": current_belt,
        "lessons": lessons,
    })

# -----------------------------
# Parent Dashboard
@login_required
def parent_dashboard(request):
    if request.user.role != 'parent':
        return redirect('home')

    # Fetch all students whose parent is the logged-in user
    linked_students = User.objects.filter(role='student', parent=request.user)

    students_data = []
    for student in linked_students:
        attempts = Attempt.objects.filter(user=student).select_related("phrase").order_by('-attempt_date')
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()
        current_belt = belt_for_correct(correct_attempts)

        # Prepare chart data for progress graph
        chart_data = []
        cum_correct = 0
        for att in attempts.order_by('attempt_date'):
            if att.is_correct:
                cum_correct += 1
            chart_data.append({
                "date": att.attempt_date.strftime("%Y-%m-%d %H:%M"),
                "correct": att.is_correct,
                "total_correct": cum_correct,
            })

        students_data.append({
            "student": student,
            "attempts": attempts[:5],  # recent 5 attempts
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "current_belt": current_belt,
            "chart_data": chart_data,
        })

    context = {
        "students_data": students_data
    }

    return render(request, "core/parent_dashboard.html", context)

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
    # Only admin users can access
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to access this page.")
        return redirect('home')

    # Get the SiteSetting object (create if it doesn't exist)
    settings_obj, created = SiteSetting.objects.get_or_create(id=1)

    if request.method == "POST":
        form = SiteSettingForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings saved successfully.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SiteSettingForm(instance=settings_obj)

    return render(request, 'core/update_site_settings.html', {'form': form})


# -----------------------------
# Parent linking
# -----------------------------

@login_required
def link_student_parent(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')

    if request.method == "POST":
        student_id = request.POST.get('student_id')
        parent_id = request.POST.get('parent_id')
        try:
            student = User.objects.get(id=student_id)
            parent = User.objects.get(id=parent_id)
            student.parent = parent
            student.save()
            messages.success(request, f"Linked {student.username} to {parent.username}.")
            return redirect('link_student_parent')  # redirect reloads with fresh data
        except User.DoesNotExist:
            messages.error(request, "Invalid student or parent.")

    students = User.objects.filter(role='student')
    parents = User.objects.filter(role='parent')
    linked_students = User.objects.filter(role='student', parent__isnull=False)
    return render(request, 'core/link_student_parent.html', {
        'students': students,
        'parents': parents,
        'linked_students': linked_students
    })


@login_required
def manage_links(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')

    linked_students = User.objects.filter(role='student', parent__isnull=False)
    return render(request, 'core/manage_links.html', {'linked_students': linked_students})


@login_required
def delete_parent_link(request, student_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    try:
        student = User.objects.get(id=student_id)
        student.parent = None
        student.save()
        messages.success(request, f"Unlinked {student.username} from parent.")
    except User.DoesNotExist:
        messages.error(request, "Invalid student.")
    return redirect('manage_links')


@login_required
def add_parent_link(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')

    if request.method == "POST":
        form = ParentLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Parent linked to student.")
        else:
            messages.error(request, "Form invalid. Please check data.")

    return redirect('link_student_parent')

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

def about_page(request):
    return render(request, "core/about.html")


def contact_page(request):
    return render(request, "core/contact.html")


def examples_page(request):
    return render(request, "core/examples.html")



# -----------------------------
# Leaderboard
# -----------------------------
@login_required
def leaderboard(request):
    students = User.objects.filter(role='student').annotate(
        total_correct=Count('attempts', filter=Q(attempts__is_correct=True))
    ).order_by('-total_correct', 'username')

    return render(request, 'core/leaderboard.html', {'students': students})


# -----------------------------
# Progress Graph (Detailed View)
# -----------------------------
@login_required
def progress_graph(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')

    # Only teacher, admin, or the student's parent can view
    if request.user.role not in ['teacher', 'admin', 'parent'] and request.user != student:
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
@login_required
def lessons(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    all_lessons = Lesson.objects.all()
    return render(request, 'core/lessons.html', {'lessons': all_lessons})

@login_required
def add_lesson(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.created_by = request.user
            lesson.save()
            messages.success(request, "Lesson added successfully!")
            return redirect('lessons')
    else:
        form = LessonForm()
    return render(request, 'core/add_lesson.html', {'form': form})

@login_required
def edit_lesson(request, lesson_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated!")
            return redirect('lessons')
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'core/add_lesson.html', {'form': form, 'edit': True})

@login_required
def delete_lesson(request, lesson_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect('home')
    lesson = get_object_or_404(Lesson, id=lesson_id)
    lesson.delete()
    messages.success(request, "Lesson deleted!")
    return redirect('lessons')

# views.py
@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'core/lesson_detail.html', {'lesson': lesson})


def leaderboard_page(request):
    # Assuming you have 'points' and 'belt' as fields in a profile model or extended User model
    students = User.objects.all().order_by('-profile.points')  # adjust if different model
    students_data = [{'username': s.username, 'points': s.profile.points, 'belt': s.profile.belt} for s in students]
    return render(request, 'leaderboard.html', {'students': students_data})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # redirect to login after successful registration
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# Decorator to allow only superusers
superuser_required = user_passes_test(lambda u: u.is_superuser)

# Add Example
@superuser_required
def add_example(request):
    if request.method == 'POST':
        form = ExampleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Example added successfully!")
            return redirect('examples_list')
    else:
        form = ExampleForm()
    return render(request, 'core/add_example.html', {'form': form, 'edit': None})

# Edit Example
@superuser_required
def edit_example(request, example_id):
    example = get_object_or_404(Example, id=example_id)
    if request.method == 'POST':
        form = ExampleForm(request.POST, request.FILES, instance=example)
        if form.is_valid():
            form.save()
            messages.success(request, "Example updated successfully!")
            return redirect('examples_list')
    else:
        form = ExampleForm(instance=example)
    return render(request, 'core/add_example.html', {'form': form, 'edit': example.title})

# Delete Example
@superuser_required
def delete_example(request, example_id):
    example = get_object_or_404(Example, id=example_id)
    if request.method == 'POST':
        example.delete()
        messages.success(request, "Example deleted successfully!")
        return redirect('examples_list')
    return render(request, 'core/delete_example.html', {'example': example})
