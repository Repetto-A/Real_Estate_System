from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from sistema_inmobiliaria import views

urlpatterns = [
    path('', views.home, name="Home"),
    path('login', views.login, name="Login"),
    path('blog', views.blog, name="Blog"),
    path('contacto', views.contacto, name="Contacto"),
    path('blog/<slug:slug>/', views.entrada, name="Entrada"),
    path('nosotros', views.nosotros, name="Nosotros"),
    path('propiedad/<int:id>/', views.propiedad, name="Propiedad"),
    path('propiedades', views.propiedades, name="Propiedades"),
    
    # Nuevas URLs para contacto y newsletter
    path('propiedad/<int:propiedad_id>/contacto/', views.contacto_propiedad, name="contacto_propiedad"),
    path('propiedad/<int:propiedad_id>/visita/', views.solicitar_visita, name="solicitar_visita"),
    path('newsletter/suscribir/', views.suscribir_newsletter, name="suscribir_newsletter"),
    path('newsletter/confirmar/<str:token>/', views.confirmar_newsletter, name="confirmar_newsletter"),
    path('newsletter/', views.newsletter_completo, name="newsletter_completo"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
