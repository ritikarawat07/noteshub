from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.utils import timezone
from django.contrib import messages
from .forms import StudentLoginForm, TeacherLoginForm, NotesUploadForm
from .models import CustomUser, Notes
from django.http import HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator

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
                return HttpResponseRedirect("/studentlogin/studentdashboard/")
            else:
                error = 'Invalid roll number or password'
        else:
            error = 'Please fill in all fields'

        return render(request, 'noteshub/studentlogin.html', {'form': form, 'error': error})

    return render(request, 'noteshub/studentlogin.html', {'form': StudentLoginForm(), 'error': None})


# ===================== STUDENT DASHBOARD =====================

@login_required(login_url='studentlogin')
def studentdashboard(request):
    if not request.user.is_student:
        return redirect('landingpage')

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
                return HttpResponseRedirect("/teacherlogin/teacherdashboard/")
            else:
                messages.error(request, "Invalid login or not authorized as teacher.")
                form = TeacherLoginForm()
                return render(request, 'noteshub/teacherlogin.html', {'form': form})
    else:
        form = TeacherLoginForm()
    return render(request, 'noteshub/teacherlogin.html', {'form': form})


# ===================== TEACHER DASHBOARD =====================
@login_required
def teacherdashboard(request):
    current_tab = request.GET.get('tab', 'pending')
    page = request.GET.get('page', 1)
    
    # Get filter parameters
    year_filter = request.GET.get('year', '')
    branch_filter = request.GET.get('branch', '')
    subject_filter = request.GET.get('subject', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset with ordering
    notes = Notes.objects.all().order_by('-uploaded_at')
    
    # Filter by tab first
    if current_tab == 'my-uploads':
        notes = notes.filter(uploader=request.user)
    elif current_tab == 'pending':
        notes = notes.filter(status='pending')
    elif current_tab == 'approved':
        notes = notes.filter(status='approved')
    elif current_tab == 'rejected':
        notes = notes.filter(status='rejected')
    
    # Then apply additional filters
    if year_filter:
        notes = notes.filter(year__icontains=year_filter)
    if branch_filter:
        notes = notes.filter(branch__icontains=branch_filter)
    if subject_filter:
        notes = notes.filter(subject__icontains=subject_filter)
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(notes, 10)
    page_obj = paginator.get_page(page)
    
    return render(request, 'noteshub/teacherdashboard.html', {
        'page_obj': page_obj,
        'current_tab': current_tab,
        'year_filter': year_filter,
        'branch_filter': branch_filter,
        'subject_filter': subject_filter,
        'search_query': search_query
    })

@login_required
def upload_note(request):
    if request.method == 'POST':
        form = NotesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            note.status = 'approved'  # Teacher uploads are auto-approved
            note.approved_by = request.user
            note.approved_at = timezone.now()
            note.save()
            messages.success(request, 'Note uploaded successfully!')
            return redirect('teacherdashboard')
    else:
        form = NotesUploadForm()
    
    return render(request, 'noteshub/teacherupload.html', {'form': form})

@login_required
def approve_note(request, note_id):
    try:
        note = Notes.objects.get(id=note_id)
        if not request.user.is_teacher:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
        
        note.status = 'approved'
        note.approved_by = request.user
        note.approved_at = timezone.now()
        note.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Note approved successfully!'})
        
        messages.success(request, 'Note approved successfully!')
        return redirect('teacherdashboard')
    except Notes.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not found'})
        messages.error(request, 'Note not found')
        return redirect('teacherdashboard')

@login_required
def reject_note(request, note_id):
    try:
        note = Notes.objects.get(id=note_id)
        if not request.user.is_teacher:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
        
        reason = request.POST.get('reason', '')
        note.status = 'rejected'
        note.rejection_reason = reason
        note.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Note rejected successfully!'})
        
        messages.success(request, 'Note rejected successfully!')
        return redirect('teacherdashboard')
    except Notes.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not found'})
        messages.error(request, 'Note not found')
        return redirect('teacherdashboard')

@login_required
def pending_note(request, note_id):
    try:
        note = Notes.objects.get(id=note_id)
        if not request.user.is_teacher:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
        
        note.status = 'pending'
        note.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Note status set to pending!'})
        
        messages.success(request, 'Note status set to pending!')
        return redirect('teacherdashboard')
    except Notes.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not found'})
        messages.error(request, 'Note not found')
        return redirect('teacherdashboard')

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    
    # Allow deletion if user is:
    # 1. The uploader
    # 2. A superuser
    # 3. A teacher (for pending notes only)
    if request.user == note.uploader or request.user.is_superuser or (request.user.is_teacher and note.status == 'pending'):
        note.delete()
        messages.success(request, 'Note deleted successfully!')
    else:
        messages.error(request, 'You do not have permission to delete this note.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Note deleted successfully!'})
    
    return redirect('teacherdashboard')

@login_required
def view_note(request, note_id):
    try:
        note = Notes.objects.get(id=note_id)
    except Notes.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not found'})
        messages.error(request, 'Note not found')
        return redirect('studentdashboard')
    
    # Only show approved notes to students, all notes to teachers
    if not request.user.is_teacher and note.status != 'approved':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not accessible'})
        messages.error(request, 'You cannot view this note as it is not approved yet.')
        return redirect('studentdashboard')
    
    # Serve the PDF file directly
    response = FileResponse(note.pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{note.subject}_{note.chapter}.pdf"'
    return response

@login_required
def download_note(request, note_id):
    try:
        note = Notes.objects.get(id=note_id)
        
        # Only allow download of approved notes to students, all notes to teachers
        if not request.user.is_teacher and note.status != 'approved':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Note not accessible'})
            messages.error(request, 'You cannot download this note as it is not approved yet.')
            return redirect('studentdashboard')
        
        # Serve the PDF file directly
        response = FileResponse(note.pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{note.subject}_{note.chapter}.pdf"'
        return response
    except Notes.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Note not found'})
        messages.error(request, 'Note not found')
        return redirect('studentdashboard')
    with open(note.file.path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{note.file.name.split("/")[-1]}"'
        return response
    return redirect('teacherdashboard')

@login_required
def studentupload(request):
    if not request.user.is_student:
        return redirect('landingpage')
    
    if request.method == 'POST':
        form = NotesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploader = request.user
            note.status = 'pending'
            note.save()
            messages.success(request, 'Note uploaded successfully and is pending approval.')
            return redirect('studentdashboard')
    else:
        form = NotesUploadForm()
    
    return render(request, 'noteshub/studentupload.html', {
        'form': form,
        'roll_number': request.user.roll_number
    })

@login_required
@user_passes_test(lambda u: u.is_teacher)
def teacherupload(request):
    if request.method == 'POST':
        form = NotesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploader = request.user
            note.status = 'approved'  # Teachers can upload directly without approval
            note.save()
            messages.success(request, 'Note uploaded successfully!')
            return redirect('teacherdashboard')
    else:
        form = NotesUploadForm()
    
    return render(request, 'noteshub/teacherupload.html', {
        'form': form,
        'username': request.user.username
    })

@login_required
def logoutview(request):
    logout(request)
    return redirect('landingpage')
