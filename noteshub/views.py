from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import StudentLoginForm, TeacherLoginForm,NotesUploadForm
from .models import CustomUser,Notes

def landingpage(request):
    return render(request, 'noteshub/landingpage.html')

# ===================== STUDENT LOGIN =====================
def studentloginview(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            roll_number = form.cleaned_data['roll_number']
            password = form.cleaned_data['password']

            user = authenticate(request, roll_number=roll_number, password=password)

            if user is not None and user.is_student:
                login(request, user)
                return redirect('studentdashboard')
            else:
                error = 'Invalid roll number or password'
        else:
            error = 'Please fill in all fields'

        return render(request, 'noteshub/studentlogin.html', {'form': form, 'error': error})

    return render(request, 'noteshub/studentlogin.html', {'form': StudentLoginForm(), 'error': None})


# ===================== STUDENT DASHBOARD =====================

@login_required(login_url='studentlogin')
def studentdashboard(request):
    if request.user.is_student:
        # Get filter values from URL query parameters
        year = request.GET.get('year')
        branch = request.GET.get('branch')
        subject = request.GET.get('subject')

        # Start with approved notes
        notes = Notes.objects.filter(status='approved')
        uploads = Notes.objects.filter(uploader=request.user)

        # Apply filters if present
        if year:
            notes = notes.filter(year=year)
        if branch:
            notes = notes.filter(branch=branch)
        if subject:
            notes = notes.filter(subject=subject)

        return render(request, 'noteshub/studentdashboard.html', {
            'roll_number': request.user.roll_number,
            'notes': notes,
            'uploads': uploads,
            'year': year,
            'branch': branch,
            'subject': subject,
        })

    return redirect('studentlogin')



# ===================== TEACHER LOGIN =====================
def teacheloginview(request):
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None and user.is_teacher:
                login(request, user)
                return redirect('teacherdashboard')
            else:
                messages.error(request, "Invalid login or not authorized as teacher.")
    else:
        form = TeacherLoginForm()
    return render(request, 'noteshub/teacherlogin.html', {'form': form})


# ===================== TEACHER DASHBOARD =====================

@login_required(login_url='teacherlogin')
def teacherdashboard(request):
    if request.user.is_teacher:
        # Get filter parameters from query
        year = request.GET.get('year')
        branch = request.GET.get('branch')
        subject = request.GET.get('subject')

        # Start with all status-based querysets
        approved_notes = Notes.objects.filter(status='approved')
        pending_notes = Notes.objects.filter(status='pending')
        rejected_notes = Notes.objects.filter(status='rejected')

        # Apply filters to all three lists
        if year:
            approved_notes = approved_notes.filter(year=year)
            pending_notes = pending_notes.filter(year=year)
            rejected_notes = rejected_notes.filter(year=year)

        if branch:
            approved_notes = approved_notes.filter(branch=branch)
            pending_notes = pending_notes.filter(branch=branch)
            rejected_notes = rejected_notes.filter(branch=branch)

        if subject:
            approved_notes = approved_notes.filter(subject=subject)
            pending_notes = pending_notes.filter(subject=subject)
            rejected_notes = rejected_notes.filter(subject=subject)

        return render(request, 'noteshub/teacherdashboard.html', {
            'approved_notes': approved_notes,
            'pending_notes': pending_notes,
            'rejected_notes': rejected_notes,
            'year': year,
            'branch': branch,
            'subject': subject,
            'uploads': Notes.objects.filter(uploader=request.user),
        })

    return redirect('teacherlogin')

# Student Upload View
@login_required(login_url='studentlogin')
def studentupload(request):
    if request.user.is_student:
        if request.method == 'POST':
            form = NotesUploadForm(request.POST, request.FILES)
            if form.is_valid():
                note = form.save(commit=False)
                note.uploader = request.user
                note.is_approved = False  # Wait for teacher approval
                note.uploaded_by_teacher = False
                note.save()
                return redirect('studentdashboard')
        else:
            form = NotesUploadForm()
        return render(request, 'noteshub/studentupload.html', {'form': form})
    return redirect('studentlogin')
# Teacher Upload View
@login_required(login_url='teacherlogin')
def teacherupload(request):
    if request.user.is_teacher:
        if request.method == 'POST':
            form = NotesUploadForm(request.POST, request.FILES)
            if form.is_valid():
                note = form.save(commit=False)
                note.uploader = request.user
                note.is_approved = True  # Instantly visible
                note.uploaded_by_teacher = True
                note.save()
                return redirect('teacherdashboard')
        else:
            form = NotesUploadForm()
        return render(request, 'noteshub/teacherupload.html', {'form': form})
    return redirect('teacherlogin')

@login_required(login_url='teacherlogin')
def approve_note(request, note_id):
    if request.user.is_teacher:
        try:
            note = Notes.objects.get(id=note_id)
            note.status = 'approved'
            note.save()
            messages.success(request, 'Note approved successfully!')
        except Notes.DoesNotExist:
            messages.error(request, 'Note not found.')
        return redirect('teacherdashboard')

@login_required(login_url='teacherlogin')
def reject_note(request, note_id):
    if request.user.is_teacher:
        try:
            note = Notes.objects.get(id=note_id)
            note.status = 'rejected'
            note.save()
            messages.success(request, 'Note rejected successfully!')
        except Notes.DoesNotExist:
            messages.error(request, 'Note not found.')
        return redirect('teacherdashboard')

@login_required(login_url='teacherlogin')
def delete_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)

    # Only allow:
    # - the uploader (if student)
    # - any teacher
    if request.user == note.uploader or request.user.is_teacher:
        note.delete()
        messages.success(request, 'Note deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this note.')

    # Redirect based on role
    if request.user.is_teacher:
        return redirect('teacherdashboard')
    else:
        return redirect('studentdashboard')


def logoutview(request):
    logout(request)
    return redirect('landingpage')
