from django.shortcuts import render

def terms_of_service(request):
    """利用規約ページ"""
    return render(request, 'legal/terms.html')

def privacy_policy(request):
    """プライバシーポリシーページ"""
    return render(request, 'legal/privacy.html')