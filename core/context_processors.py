from .models import SiteSetting

def site_settings(request):
    return {
        "SITE": SiteSetting.get()
    }
