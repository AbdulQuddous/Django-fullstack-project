from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from tasks.models import Task, ActivityLog
from accounts.models import User


@login_required
def index(request):
    if request.user.is_admin_user:
        return admin_dashboard(request)
    return employee_dashboard(request)


@login_required
def employee_dashboard(request):
    user = request.user
    user_tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user)
    ).select_related('assigned_to', 'created_by')

    now = timezone.now()
    upcoming_deadline = now + timedelta(days=3)

    total = user_tasks.count()
    completed = user_tasks.filter(status='completed').count()
    pending = user_tasks.filter(status='pending').count()
    in_progress = user_tasks.filter(status='in_progress').count()
    high_priority = user_tasks.filter(priority__in=['high', 'urgent']).count()
    overdue = sum(1 for t in user_tasks if t.is_overdue)

    recent_tasks = user_tasks.order_by('-created_at')[:5]
    upcoming_tasks = user_tasks.filter(
        deadline__gte=now,
        deadline__lte=upcoming_deadline,
        status__in=['pending', 'in_progress']
    ).order_by('deadline')[:5]

    # Chart data
    status_data = {
        'labels': ['Pending', 'In Progress', 'Completed', 'Cancelled'],
        'data': [
            user_tasks.filter(status='pending').count(),
            user_tasks.filter(status='in_progress').count(),
            user_tasks.filter(status='completed').count(),
            user_tasks.filter(status='cancelled').count(),
        ]
    }

    context = {
        'total_tasks': total,
        'completed_tasks': completed,
        'pending_tasks': pending,
        'in_progress_tasks': in_progress,
        'high_priority_tasks': high_priority,
        'overdue_tasks': overdue,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'status_data': status_data,
        'completion_rate': round((completed / total * 100) if total > 0 else 0),
    }
    return render(request, 'dashboard/employee_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if not request.user.is_admin_user:
        return redirect('dashboard:employee')

    all_tasks = Task.objects.select_related('assigned_to', 'created_by')
    all_users = User.objects.filter(is_active=True)
    now = timezone.now()

    total_users = all_users.count()
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status='completed').count()
    pending_tasks = all_tasks.filter(status='pending').count()
    in_progress_tasks = all_tasks.filter(status='in_progress').count()
    overdue_tasks = sum(1 for t in all_tasks if t.is_overdue)

    # Per-user task stats
    user_stats = []
    for user in all_users.filter(role='employee')[:8]:
        utasks = Task.objects.filter(assigned_to=user)
        user_stats.append({
            'user': user,
            'total': utasks.count(),
            'completed': utasks.filter(status='completed').count(),
            'pending': utasks.filter(status='pending').count(),
        })

    # Monthly data for last 6 months
    monthly_labels = []
    monthly_created = []
    monthly_completed = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0)
        if i > 0:
            month_end = (now - timedelta(days=30*(i-1))).replace(day=1, hour=0, minute=0)
        else:
            month_end = now
        monthly_labels.append(month_start.strftime('%b'))
        monthly_created.append(all_tasks.filter(created_at__gte=month_start, created_at__lt=month_end).count())
        monthly_completed.append(all_tasks.filter(completed_at__gte=month_start, completed_at__lt=month_end).count())

    recent_activity = ActivityLog.objects.select_related('task', 'user').order_by('-created_at')[:10]
    recent_tasks = all_tasks.order_by('-created_at')[:8]

    context = {
        'total_users': total_users,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'user_stats': user_stats,
        'recent_activity': recent_activity,
        'recent_tasks': recent_tasks,
        'monthly_labels': monthly_labels,
        'monthly_created': monthly_created,
        'monthly_completed': monthly_completed,
        'priority_data': {
            'labels': ['Low', 'Medium', 'High', 'Urgent'],
            'data': [
                all_tasks.filter(priority='low').count(),
                all_tasks.filter(priority='medium').count(),
                all_tasks.filter(priority='high').count(),
                all_tasks.filter(priority='urgent').count(),
            ]
        },
        'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
