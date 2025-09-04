from .models import SiteSetting

def site_settings(_request):
    return {"SITE": SiteSetting.get()}
