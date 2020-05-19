from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class LocaleMiddleware(MiddlewareMixin):
    """
    Parse a request and decide what translation object to install in the
    current thread context. This allows pages to be dynamically translated to
    the language the user desires (if the language is available, of course).
    """

    def process_request(self, request):

        language = translation.get_language_from_request(request)

        language_qs = request.GET.get("locale", None)

        if language_qs:
            language = language_qs

        # fallback to default language
        if not language:
            language = settings.LANGUAGE_CODE

        translation.activate(language)

        request.LANGUAGE_CODE = translation.get_language()
