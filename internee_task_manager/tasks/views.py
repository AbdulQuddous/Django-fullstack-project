from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
import csv
from .models import Task, Comment, ActivityLog, Tag
from .forms import TaskForm, CommentForm, TaskFilterForm
from accounts.models import User


def log_activity(task, user, action):
    ActivityLog.objects.create(task=task, user=user, action=action)


@login_required
def task_list(request):
    if request.user.is_admin_user:
        tasks = Task.objects.select_related('assigned_to', 'created_by').prefetch_related('tags')
    else:
        tasks = Task.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user)
        ).select_related('assigned_to', 'created_by').prefetch_related('tags')

    form = TaskFilterForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        priority = form.cleaned_data.get('priority')
        assigned_to = form.cleaned_data.get('assigned_to')
        if search:
            tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if status:
            tasks = tasks.filter(status=status)
        if priority:
            tasks = tasks.filter(priority=priority)
        if assigned_to:
            tasks = tasks.filter(assigned_to=assigned_to)

    paginator = Paginator(tasks, 10)
    page = request.GET.get('page', 1)
    tasks = paginator.get_page(page)

    return render(request, 'tasks/task_list.html', {'tasks': tasks, 'filter_form': form})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()
            log_activity(task, request.user, f'Created task "{task.title}"')
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:detail', pk=task.pk)
    else:
        form = TaskForm(user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_admin_user and task.assigned_to != request.user and task.created_by != request.user:
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('tasks:list')
    
    comment_form = CommentForm()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            log_activity(task, request.user, 'Added a comment')
            messages.success(request, 'Comment added!')
            return redirect('tasks:detail', pk=pk)
    
    context = {
        'task': task,
        'comments': task.comments.select_related('user'),
        'activity_logs': task.activity_logs.select_related('user')[:10],
        'comment_form': comment_form,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_admin_user and task.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('tasks:detail', pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task, user=request.user)
        if form.is_valid():
            old_status = task.status
            task = form.save()
            if old_status != task.status:
                log_activity(task, request.user, f'Changed status from {old_status} to {task.status}')
            else:
                log_activity(task, request.user, f'Updated task details')
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks:detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'task': task, 'action': 'Update'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_admin_user and task.created_by != request.user:
        messages.error(request, 'You do not have permission to delete this task.')
        return redirect('tasks:detail', pk=pk)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('tasks:list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_update_status(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            task.save()
            log_activity(task, request.user, f'Changed status from {old_status} to {new_status}')
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False})


@login_required
def kanban_view(request):
    if request.user.is_admin_user:
        base_qs = Task.objects.select_related('assigned_to')
    else:
        base_qs = Task.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user)
        ).select_related('assigned_to')

    context = {
        'pending_tasks': base_qs.filter(status='pending'),
        'in_progress_tasks': base_qs.filter(status='in_progress'),
        'completed_tasks': base_qs.filter(status='completed'),
    }
    return render(request, 'tasks/kanban.html', context)


@login_required
def export_tasks_csv(request):
    if not request.user.is_admin_user:
        messages.error(request, 'Admin access required.')
        return redirect('tasks:list')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Assigned To', 'Created By', 'Deadline', 'Created At'])
    for task in Task.objects.select_related('assigned_to', 'created_by'):
        writer.writerow([
            task.id, task.title, task.status, task.priority,
            task.assigned_to.username if task.assigned_to else 'Unassigned',
            task.created_by.username,
            task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else '',
            task.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response
