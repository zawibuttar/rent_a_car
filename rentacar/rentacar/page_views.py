from django.shortcuts import render

def home(request):
    from accounts.hero_banners import get_random_hero_banner_url, get_hero_banner_fallback_url
    return render(request, 'home.html', {
        'hero_banner_url': get_random_hero_banner_url(request),
        'hero_banner_fallback': get_hero_banner_fallback_url(),
    })

def car_list(request):
    return render(request, 'cars/car_list.html')

def car_detail(request, pk):
    return render(request, 'cars/car_detail.html', {'car_id': pk})

# Auth pages
def login_page(request):
    return render(request, 'accounts/login.html')

def register_page(request):
    return render(request, 'accounts/register.html')

# Dashboard pages
def customer_dashboard(request):
    return render(request, 'dashboards/customer_dashboard.html')

def owner_dashboard(request):
    return render(request, 'dashboards/owner_dashboard.html')

def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')

def admin_social_media(request):
    from django.shortcuts import redirect
    from django.http import HttpResponseForbidden
    if not request.user.is_authenticated:
        return redirect('login-page')
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        return HttpResponseForbidden("You do not have permission to access this page.")
    return render(request, 'dashboards/admin_social_media.html')

def admin_hero_banners(request):
    from django.shortcuts import redirect
    from django.http import HttpResponseForbidden
    if not request.user.is_authenticated:
        return redirect('login-page')
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        return HttpResponseForbidden("You do not have permission to access this page.")
    return render(request, 'dashboards/admin_hero_banners.html')

def main_dashboard(request):

    from django.shortcuts import redirect
    if not request.user.is_authenticated:
        return redirect('login-page')
    
    if getattr(request.user, 'is_customer', False):
        return redirect('customer-dashboard')
    elif getattr(request.user, 'is_owner', False):
        return redirect('owner-dashboard')
    elif getattr(request.user, 'is_admin', False) or request.user.is_superuser:
        return redirect('admin-dashboard')
    
    return redirect('home')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def contact(request):
    return render(request, 'contact.html')
