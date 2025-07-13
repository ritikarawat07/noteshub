from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import StudentLoginForm, TeacherLoginForm, NotesUploadForm
from .models import CustomUser, Notes
from django.http import HttpResponseRedirect, JsonResponse

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

@login_required(login_url='teacherlogin')
def teacherdashboard(request):
    from .models import Notes
    
    def serialize_note(note):
        uploader_name = note.uploader.username if note.uploader else 'Unknown User'
        return {
            'id': note.id,
            'subject': note.subject,
            'chapter': note.chapter,
            'year': note.year,
            'branch': note.branch,
            'pdf_url': note.pdf.url,
            'pdf_size': note.pdf.size,  # Add PDF size in bytes
            'status': note.status,
            'uploaded_at': note.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'uploader_name': uploader_name
        }
    
    # Get all notes with debug logging
    print(f"\n=== DEBUG: Teacher Dashboard Request ===")
    print(f"Current User: {request.user} (ID: {request.user.id})")
    
    # Show only my uploads in 'my_uploads'
    my_uploads = Notes.objects.filter(uploader=request.user)
    
    # Show all notes (both teacher and student uploaded) in other sections
    pending_notes = Notes.objects.filter(status='pending')
    approved_notes = Notes.objects.filter(status='approved')
    rejected_notes = Notes.objects.filter(status='rejected')
    
    print(f"My Uploads Count: {my_uploads.count()}")
    print(f"Pending Notes Count: {pending_notes.count()}")
    print(f"Approved Notes Count: {approved_notes.count()}")
    print(f"Rejected Notes Count: {rejected_notes.count()}")
    print("===============================\n")
    
    # Prepare data for response
    data = {
        'my_uploads': [serialize_note(note) for note in my_uploads],
        'pending_notes': [serialize_note(note) for note in pending_notes],
        'approved_notes': [serialize_note(note) for note in approved_notes],
        'rejected_notes': [serialize_note(note) for note in rejected_notes],
    }

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)


    # Return HTML for regular requests
    context = {
        'my_uploads': json.dumps(data['my_uploads']),
        'pending_notes': json.dumps(data['pending_notes']),
        'approved_notes': json.dumps(data['approved_notes']),
        'rejected_notes': json.dumps(data['rejected_notes']),
    }

    return render(request, 'noteshub/teacherdashboard.html', context)
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
                return HttpResponseRedirect("/studentlogin/studentdashboard/")
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
                note.status = 'pending'  # Notes from teachers go to pending for review
                note.save()
                messages.success(request, 'Note uploaded successfully!')
                return HttpResponseRedirect("/teacherlogin/teacherdashboard/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = NotesUploadForm()
        return render(request, 'noteshub/teacherupload.html', {
            'form': form,
            'title': 'Teacher Upload'
        })
    return redirect('teacherlogin')

@login_required(login_url='teacherlogin')
def view_note(request, note_id):
    try:
        note = get_object_or_404(Notes, id=note_id)
        if not request.user.is_teacher:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        # Serve the PDF file directly
        response = HttpResponse(note.pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{note.pdf.name.split('/')[-1]}"'
        return response
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error viewing note: {str(e)}'
        }, status=500)

@login_required(login_url='teacherlogin')
def download_note(request, note_id):
    try:
        note = get_object_or_404(Notes, id=note_id)
        if not request.user.is_teacher:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        # Serve the PDF file directly with download disposition
        response = HttpResponse(note.pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{note.pdf.name.split('/')[-1]}"'
        return response
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error downloading note: {str(e)}'
        }, status=500)

@login_required(login_url='teacherlogin')
def approve_note(request, note_id):
    if not request.user.is_teacher:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            note = Notes.objects.get(id=note_id)
            note.status = 'approved'
            note.save()
            
            # Return JSON response for AJAX request
            return JsonResponse({
                'success': True, 
                'message': 'Note approved successfully!',
                'note': {
                    'id': note.id,
                    'subject': note.subject,
                    'chapter': note.chapter,
                    'year': note.year,
                    'branch': note.branch,
                    'status': note.status,
                    'uploaded_at': note.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=200)
            
        except Notes.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Note not found.'}, status=404)
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required(login_url='teacherlogin')
def reject_note(request, note_id):
    if not request.user.is_teacher:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            note = Notes.objects.get(id=note_id)
            
            # Check if the note is in a valid state for rejection
            if note.status == 'approved':
                return JsonResponse({'success': False, 'message': 'Cannot reject an approved note!'}, status=400)
                
            # Get rejection reason from request body
            data = json.loads(request.body)
            reason = data.get('reason', 'No reason provided')
            
            # Update the note status
            note.status = 'rejected'
            
            # If the model has rejection_reason field, store the reason
            if hasattr(note, 'rejection_reason'):
                note.rejection_reason = reason[:255]
                
            note.save()
            
            # Prepare note data for response
            note_data = {
                'id': note.id,
                'subject': note.subject,
                'chapter': note.chapter,
                'year': note.year,
                'branch': note.branch,
                'status': note.status,
                'pdf_url': note.pdf.url,
                'uploaded_at': note.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'uploader_name': note.uploader.username
            }
            
            # Include rejection reason in the note data if it exists
            if hasattr(note, 'rejection_reason'):
                note_data['rejection_reason'] = note.rejection_reason
            
            # Return success response with note data
            return JsonResponse({
                'success': True, 
                'message': 'Note rejected successfully!',
                'note': note_data
            }, status=200)
            
        except Notes.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Note not found!'}, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

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
        return HttpResponseRedirect("/teacherlogin/teacherdashboard/")
    else:
        return HttpResponseRedirect("/studentlogin/studentdashboard/")


def logoutview(request):
    logout(request)
    return HttpResponseRedirect("/landingpage/")
