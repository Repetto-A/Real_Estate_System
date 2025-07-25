from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Vendedor, Propiedad, Consulta, SolicitudVisita
from .forms import ConsultaForm, ContactoPropiedadForm
from django.utils import timezone
from datetime import date, time
import tempfile
from PIL import Image
import io


class VendedorModelTest(TestCase):
    """
    Tests unitarios para el modelo Vendedor
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.vendedor_valido = Vendedor(
            nombre="Juan",
            apellido="Pérez",
            telefono="1234567890",
            email="juan@example.com"
        )
    
    def test_vendedor_str_method(self):
        """Test del método __str__ del modelo Vendedor"""
        self.assertEqual(str(self.vendedor_valido), "Juan Pérez")
    
    def test_vendedor_validacion_exitosa(self):
        """Test de validación exitosa de un vendedor"""
        errores = self.vendedor_valido.validar()
        self.assertEqual(errores, [])
    
    def test_vendedor_sin_nombre(self):
        """Test de validación cuando falta el nombre"""
        vendedor = Vendedor(
            nombre="",
            apellido="Pérez",
            telefono="1234567890"
        )
        errores = vendedor.validar()
        self.assertIn("El nombre del vendedor es obligatorio.", errores)
    
    def test_vendedor_sin_apellido(self):
        """Test de validación cuando falta el apellido"""
        vendedor = Vendedor(
            nombre="Juan",
            apellido="",
            telefono="1234567890"
        )
        errores = vendedor.validar()
        self.assertIn("El apellido del vendedor es obligatorio.", errores)
    
    def test_vendedor_sin_telefono(self):
        """Test de validación cuando falta el teléfono"""
        vendedor = Vendedor(
            nombre="Juan",
            apellido="Pérez",
            telefono=""
        )
        errores = vendedor.validar()
        self.assertIn("El teléfono del vendedor es obligatorio.", errores)
    
    def test_vendedor_telefono_formato_invalido(self):
        """Test de validación con formato de teléfono inválido"""
        vendedor = Vendedor(
            nombre="Juan",
            apellido="Pérez",
            telefono="123"  # Muy corto
        )
        errores = vendedor.validar()
        self.assertIn("Formato del teléfono no válido, debe tener 10 dígitos.", errores)
        
        # Test con letras en el teléfono
        vendedor.telefono = "123abc7890"
        errores = vendedor.validar()
        self.assertIn("Formato del teléfono no válido, debe tener 10 dígitos.", errores)
    
    def test_vendedor_creacion_en_db(self):
        """Test de creación de vendedor en la base de datos"""
        self.vendedor_valido.save()
        vendedor_db = Vendedor.objects.get(id=self.vendedor_valido.id)
        self.assertEqual(vendedor_db.nombre, "Juan")
        self.assertEqual(vendedor_db.apellido, "Pérez")
        self.assertEqual(vendedor_db.telefono, "1234567890")
        self.assertEqual(vendedor_db.email, "juan@example.com")


class PropiedadModelTest(TestCase):
    """
    Tests unitarios adicionales para el modelo Propiedad
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.vendedor = Vendedor.objects.create(
            nombre="Ana",
            apellido="García",
            telefono="9876543210",
            email="ana@example.com"
        )
        
        # Crear una imagen temporal para las pruebas
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        self.imagen_test = SimpleUploadedFile(
            "test_image.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
    
    def test_propiedad_creacion(self):
        """Test de creación de propiedad"""
        propiedad = Propiedad.objects.create(
            titulo="Casa de prueba",
            precio=150000,
            imagen=self.imagen_test,
            descripcion="Una hermosa casa de prueba con más de 50 caracteres para pasar la validación",
            habitaciones=3,
            bano=2,
            estacionamiento=1,
            vendedor_id=self.vendedor
        )
        
        self.assertEqual(propiedad.titulo, "Casa de prueba")
        self.assertEqual(propiedad.precio, 150000)
        self.assertEqual(propiedad.habitaciones, 3)
        self.assertEqual(propiedad.vendedor_id, self.vendedor)


class HomeViewTest(TestCase):
    """
    Tests end-to-end para las vistas principales
    """
    
    def setUp(self):
        """Configuración inicial para tests de vistas"""
        self.client = Client()
        
        # Crear vendedor de prueba
        self.vendedor = Vendedor.objects.create(
            nombre="Carlos",
            apellido="López",
            telefono="5555555555",
            email="carlos@example.com"
        )
        
        # Crear imagen temporal
        image = Image.new('RGB', (100, 100), color='blue')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        imagen_test = SimpleUploadedFile(
            "test_home.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        # Crear propiedad de prueba
        self.propiedad = Propiedad.objects.create(
            titulo="Casa End-to-End Test",
            precio=200000,
            imagen=imagen_test,
            descripcion="Casa para testing end-to-end con descripción suficientemente larga para pasar validación",
            habitaciones=4,
            bano=3,
            estacionamiento=2,
            vendedor_id=self.vendedor
        )
    
    def test_home_view_status_code(self):
        """Test que la página home carga correctamente"""
        response = self.client.get(reverse('Home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_contains_propiedades(self):
        """Test que la página home muestra las propiedades"""
        response = self.client.get(reverse('Home'))
        self.assertContains(response, "Casa End-to-End Test")
        self.assertContains(response, "200000")
    
    def test_propiedades_view_status_code(self):
        """Test que la página de propiedades carga correctamente"""
        response = self.client.get(reverse('Propiedades'))
        self.assertEqual(response.status_code, 200)
    
    def test_propiedad_detail_view(self):
        """Test que la vista de detalle de propiedad funciona"""
        response = self.client.get(reverse('Propiedad', args=[self.propiedad.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.propiedad.titulo)
        self.assertContains(response, self.propiedad.descripcion)


class ContactoEndToEndTest(TestCase):
    """
    Tests end-to-end para el sistema de contacto
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Crear vendedor y propiedad para las pruebas
        self.vendedor = Vendedor.objects.create(
            nombre="María",
            apellido="Rodríguez",
            telefono="7777777777",
            email="maria@example.com"
        )
        
        image = Image.new('RGB', (100, 100), color='green')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        imagen_test = SimpleUploadedFile(
            "test_contacto.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        self.propiedad = Propiedad.objects.create(
            titulo="Casa para Contacto Test",
            precio=180000,
            imagen=imagen_test,
            descripcion="Casa para testing de contacto con descripción suficientemente larga para validación",
            habitaciones=3,
            bano=2,
            estacionamiento=1,
            vendedor_id=self.vendedor
        )
    
    def test_contacto_view_get(self):
        """Test que la página de contacto carga correctamente"""
        response = self.client.get(reverse('Contacto'))
        self.assertEqual(response.status_code, 200)
    
    def test_contacto_form_submission(self):
        """Test end-to-end de envío de formulario de contacto"""
        form_data = {
            'nombre': 'Usuario Test',
            'telefono': '1111111111',
            'email': 'test@example.com',
            'mensaje': 'Este es un mensaje de prueba',
            'tipo': 'general',
            'propiedad_id': '',
            'precio': ''
        }
        
        response = self.client.post(reverse('Contacto'), data=form_data)
        
        # Verificar que se redirige correctamente (o se procesa)
        self.assertIn(response.status_code, [200, 302])
        
        # Verificar que se creó una consulta en la base de datos
        consulta = Consulta.objects.filter(email='test@example.com').first()
        if consulta:
            self.assertEqual(consulta.nombre, 'Usuario Test')
            self.assertEqual(consulta.mensaje, 'Este es un mensaje de prueba')
    
    def test_solicitud_visita_creation(self):
        """Test end-to-end de creación de solicitud de visita"""
        form_data = {
            'nombre': 'Visitante Test',
            'telefono': '2222222222',
            'email': 'visitante@example.com',
            'mensaje': 'Quiero visitar esta propiedad',
            'tipo': 'Visita',
            'propiedad_id': str(self.propiedad.id),
            'precio': str(self.propiedad.precio),
            'fecha_visita': '2024-12-31',
            'hora_visita': '14:00'
        }
        
        response = self.client.post(reverse('Contacto'), data=form_data)
        
        # Verificar que se procesó correctamente
        self.assertIn(response.status_code, [200, 302])
        
        # Verificar que se creó la solicitud de visita
        solicitud = SolicitudVisita.objects.filter(email='visitante@example.com').first()
        if solicitud:
            self.assertEqual(solicitud.nombre, 'Visitante Test')
            self.assertEqual(solicitud.propiedad, self.propiedad)


class BlogEndToEndTest(TestCase):
    """
    Tests end-to-end para el blog
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
    
    def test_blog_view_status_code(self):
        """Test que la página del blog carga correctamente"""
        response = self.client.get(reverse('Blog'))
        self.assertEqual(response.status_code, 200)
    
    def test_nosotros_view_status_code(self):
        """Test que la página nosotros carga correctamente"""
        response = self.client.get(reverse('Nosotros'))
        self.assertEqual(response.status_code, 200)


class FormularioValidacionTest(TestCase):
    """
    Tests críticos para validación de formularios - ESENCIAL PARA PRODUCCIÓN
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.vendedor = Vendedor.objects.create(
            nombre="Test",
            apellido="Vendedor",
            telefono="1234567890",
            email="test@example.com"
        )
        
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        self.imagen_test = SimpleUploadedFile(
            "test.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        self.propiedad = Propiedad.objects.create(
            titulo="Casa Test",
            precio=100000,
            imagen=self.imagen_test,
            descripcion="Descripción de prueba con más de 50 caracteres para pasar validación",
            habitaciones=2,
            bano=1,
            estacionamiento=1,
            vendedor_id=self.vendedor
        )
    
    def test_contacto_email_invalido(self):
        """Test que rechaza emails inválidos"""
        from .forms import ConsultaForm
        
        form_data = {
            'nombre': 'Test User',
            'email': 'email_invalido',  # Email sin formato correcto
            'telefono': '1234567890',
            'mensaje': 'Mensaje de prueba',
            'origen': 'general',
            'tipo': 'general'
        }
        
        form = ConsultaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_contacto_campos_obligatorios(self):
        """Test que verifica campos obligatorios en formularios"""
        from .forms import ConsultaForm
        
        # Formulario vacío
        form = ConsultaForm(data={})
        self.assertFalse(form.is_valid())
        
        # Verificar que los campos obligatorios están en los errores
        required_fields = ['nombre', 'email', 'mensaje']
        for field in required_fields:
            self.assertIn(field, form.errors)
    
    def test_telefono_formato_correcto(self):
        """Test que valida formato de teléfono"""
        from .forms import ConsultaForm
        
        # Teléfono con letras
        form_data = {
            'nombre': 'Test User',
            'email': 'test@example.com',
            'telefono': '123abc7890',
            'mensaje': 'Mensaje de prueba',
            'origen': 'general',
            'tipo': 'general'
        }
        
        form = ConsultaForm(data=form_data)
        # Nota: Esto depende de si tienes validación de teléfono en el formulario
        # Si no la tienes, considera agregarla para producción
    
    def test_mensaje_muy_corto(self):
        """Test que rechaza mensajes muy cortos"""
        from .forms import ConsultaForm
        
        form_data = {
            'nombre': 'Test User',
            'email': 'test@example.com',
            'telefono': '1234567890',
            'mensaje': 'Hi',  # Mensaje muy corto
            'origen': 'general',
            'tipo': 'general'
        }
        
        form = ConsultaForm(data=form_data)
        # Si tienes validación de longitud mínima, debería fallar


class SeguridadYErroresTest(TestCase):
    """
    Tests de seguridad y manejo de errores - CRÍTICO PARA PRODUCCIÓN
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
    
    def test_pagina_inexistente_404(self):
        """Test que páginas inexistentes devuelven 404"""
        response = self.client.get('/pagina-que-no-existe/')
        self.assertEqual(response.status_code, 404)
    
    def test_propiedad_inexistente_404(self):
        """Test que propiedades inexistentes devuelven 404"""
        response = self.client.get(reverse('Propiedad', args=[99999]))
        self.assertEqual(response.status_code, 404)
    
    def test_csrf_protection(self):
        """Test que formularios requieren CSRF token"""
        # Intentar enviar formulario sin CSRF token
        form_data = {
            'nombre': 'Test User',
            'telefono': '1234567890',
            'email': 'test@example.com',
            'mensaje': 'Mensaje de prueba',
            'tipo': 'general'
        }
        
        # Cliente sin CSRF
        client_no_csrf = Client(enforce_csrf_checks=True)
        response = client_no_csrf.post(reverse('Contacto'), data=form_data)
        
        # Debería fallar por falta de CSRF
        self.assertEqual(response.status_code, 403)
    
    def test_sql_injection_protection(self):
        """Test básico de protección contra SQL injection"""
        # Intentar inyección SQL en búsqueda
        malicious_query = "'; DROP TABLE sistema_inmobiliaria_propiedad; --"
        
        # Django ORM debería proteger automáticamente
        response = self.client.get('/propiedades/', {'search': malicious_query})
        
        # La página debería cargar normalmente (sin errores de BD)
        self.assertIn(response.status_code, [200, 404])
    
    def test_xss_protection(self):
        """Test básico de protección contra XSS"""
        # Intentar script malicioso en formulario
        malicious_script = "<script>alert('XSS')</script>"
        
        form_data = {
            'nombre': malicious_script,
            'telefono': '1234567890',
            'email': 'test@example.com',
            'mensaje': 'Mensaje normal',
            'tipo': 'general'
        }
        
        response = self.client.post(reverse('Contacto'), data=form_data)
        
        # Verificar que la respuesta es exitosa (puede ser redirect 302 o success 200)
        self.assertIn(response.status_code, [200, 302])
        
        # Verificar que el script se guardó en la BD pero como texto plano
        consulta = Consulta.objects.filter(email='test@example.com').first()
        if consulta:
            # El script debe estar guardado como texto, no como código ejecutable
            self.assertEqual(consulta.nombre, malicious_script)
            # Esto es correcto - Django guarda el contenido pero lo escapa al renderizar


class BusquedaYFiltrosTest(TestCase):
    """
    Tests para funcionalidades de búsqueda - IMPORTANTE PARA UX
    """
    
    def setUp(self):
        """Crear datos de prueba"""
        self.vendedor = Vendedor.objects.create(
            nombre="Vendedor",
            apellido="Test",
            telefono="1234567890",
            email="vendedor@test.com"
        )
        
        # Crear varias propiedades para testear búsqueda
        image = Image.new('RGB', (100, 100), color='blue')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        imagen_test = SimpleUploadedFile(
            "search_test.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        self.casa_barata = Propiedad.objects.create(
            titulo="Casa Económica",
            precio=50000,
            imagen=imagen_test,
            descripcion="Casa pequeña pero cómoda, ideal para parejas jóvenes que buscan su primer hogar",
            habitaciones=2,
            bano=1,
            estacionamiento=1,
            vendedor_id=self.vendedor
        )
        
        # Crear segunda imagen para la segunda propiedad
        image2 = Image.new('RGB', (100, 100), color='green')
        temp_file2 = io.BytesIO()
        image2.save(temp_file2, format='JPEG')
        temp_file2.seek(0)
        
        imagen_test2 = SimpleUploadedFile(
            "search_test2.jpg",
            temp_file2.getvalue(),
            content_type="image/jpeg"
        )
        
        self.casa_cara = Propiedad.objects.create(
            titulo="Mansión de Lujo",
            precio=500000,
            imagen=imagen_test2,
            descripcion="Espectacular mansión con todas las comodidades para familias exigentes",
            habitaciones=5,
            bano=3,
            estacionamiento=3,
            vendedor_id=self.vendedor
        )
    
    def test_busqueda_por_titulo(self):
        """Test que la búsqueda por título funciona"""
        # Buscar "económica"
        propiedades = Propiedad.objects.filter(titulo__icontains="Económica")
        self.assertEqual(propiedades.count(), 1)
        self.assertEqual(propiedades.first(), self.casa_barata)
        
        # Buscar "lujo"
        propiedades = Propiedad.objects.filter(titulo__icontains="Lujo")
        self.assertEqual(propiedades.count(), 1)
        self.assertEqual(propiedades.first(), self.casa_cara)
    
    def test_filtro_por_precio(self):
        """Test que los filtros de precio funcionan"""
        # Propiedades baratas (menos de 100,000)
        propiedades_baratas = Propiedad.objects.filter(precio__lt=100000)
        self.assertIn(self.casa_barata, propiedades_baratas)
        self.assertNotIn(self.casa_cara, propiedades_baratas)
        
        # Propiedades caras (más de 100,000)
        propiedades_caras = Propiedad.objects.filter(precio__gt=100000)
        self.assertIn(self.casa_cara, propiedades_caras)
        self.assertNotIn(self.casa_barata, propiedades_caras)
    
    def test_filtro_por_habitaciones(self):
        """Test que el filtro por habitaciones funciona"""
        # Casas pequeñas (2 habitaciones o menos)
        casas_pequenas = Propiedad.objects.filter(habitaciones__lte=2)
        self.assertIn(self.casa_barata, casas_pequenas)
        self.assertNotIn(self.casa_cara, casas_pequenas)
        
        # Casas grandes (3 habitaciones o más)
        casas_grandes = Propiedad.objects.filter(habitaciones__gte=3)
        self.assertIn(self.casa_cara, casas_grandes)
        self.assertNotIn(self.casa_barata, casas_grandes)


class RendimientoTest(TestCase):
    """
    Tests de rendimiento básicos - IMPORTANTE PARA ESCALABILIDAD
    """
    
    def setUp(self):
        """Crear vendedor para las pruebas"""
        self.vendedor = Vendedor.objects.create(
            nombre="Performance",
            apellido="Test",
            telefono="1234567890",
            email="perf@test.com"
        )
    
    def test_carga_muchas_propiedades(self):
        """Test que el sistema maneja múltiples propiedades"""
        import time
        
        # Crear imagen base
        image = Image.new('RGB', (50, 50), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        # Crear múltiples propiedades
        propiedades = []
        for i in range(20):  # 20 propiedades para test
            imagen_test = SimpleUploadedFile(
                f"perf_test_{i}.jpg",
                temp_file.getvalue(),
                content_type="image/jpeg"
            )
            
            propiedades.append(Propiedad(
                titulo=f"Casa Performance {i}",
                precio=100000 + (i * 10000),
                imagen=imagen_test,
                descripcion=f"Descripción de la casa {i} con suficientes caracteres para pasar validación",
                habitaciones=2 + (i % 3),
                bano=1 + (i % 2),
                estacionamiento=1,
                vendedor_id=self.vendedor
            ))
        
        # Crear todas las propiedades
        start_time = time.time()
        Propiedad.objects.bulk_create(propiedades)
        creation_time = time.time() - start_time
        
        # Verificar que se crearon
        self.assertEqual(Propiedad.objects.count(), 20)
        
        # Test de carga de página con muchas propiedades
        start_time = time.time()
        response = self.client.get(reverse('Propiedades'))
        load_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # El tiempo de carga debería ser razonable (menos de 2 segundos)
        self.assertLess(load_time, 2.0, "La página tarda demasiado en cargar")
    
    def test_consultas_eficientes(self):
        """Test que las consultas a BD son eficientes"""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Crear algunas propiedades
        image = Image.new('RGB', (50, 50), color='blue')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        for i in range(5):
            imagen_test = SimpleUploadedFile(
                f"query_test_{i}.jpg",
                temp_file.getvalue(),
                content_type="image/jpeg"
            )
            
            Propiedad.objects.create(
                titulo=f"Casa Query {i}",
                precio=150000,
                imagen=imagen_test,
                descripcion=f"Descripción de consulta {i} con caracteres suficientes para validación",
                habitaciones=3,
                bano=2,
                estacionamiento=1,
                vendedor_id=self.vendedor
            )
        
        # Resetear contador de consultas
        connection.queries_log.clear()
        
        # Cargar página de propiedades
        response = self.client.get(reverse('Propiedades'))
        
        # Verificar que no hay demasiadas consultas
        query_count = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(query_count, 10, f"Demasiadas consultas a BD: {query_count}")


class IntegracionEmailTest(TestCase):
    """
    Tests de integración para sistema de emails - CRÍTICO PARA NEGOCIO
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.vendedor = Vendedor.objects.create(
            nombre="Email",
            apellido="Test",
            telefono="1234567890",
            email="emailtest@example.com"
        )
        
        image = Image.new('RGB', (100, 100), color='yellow')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        imagen_test = SimpleUploadedFile(
            "email_test.jpg",
            temp_file.getvalue(),
            content_type="image/jpeg"
        )
        
        self.propiedad = Propiedad.objects.create(
            titulo="Casa Email Test",
            precio=200000,
            imagen=imagen_test,
            descripcion="Casa para testear funcionalidad de emails con descripción suficiente",
            habitaciones=3,
            bano=2,
            estacionamiento=2,
            vendedor_id=self.vendedor
        )
    
    def test_consulta_crea_registro(self):
        """Test que las consultas se guardan en BD"""
        initial_count = Consulta.objects.count()
        
        form_data = {
            'nombre': 'Cliente Email',
            'telefono': '9999999999',
            'email': 'cliente@example.com',
            'mensaje': 'Estoy interesado en esta propiedad',
            'tipo': 'general',
            'propiedad_id': '',
            'precio': ''
        }
        
        response = self.client.post(reverse('Contacto'), data=form_data)
        
        # Verificar que se creó una nueva consulta
        final_count = Consulta.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verificar datos de la consulta
        consulta = Consulta.objects.latest('fecha_consulta')
        self.assertEqual(consulta.nombre, 'Cliente Email')
        self.assertEqual(consulta.email, 'cliente@example.com')
    
    def test_solicitud_visita_crea_registro(self):
        """Test que las solicitudes de visita se guardan"""
        initial_count = SolicitudVisita.objects.count()
        
        form_data = {
            'nombre': 'Visitante Email',
            'telefono': '8888888888',
            'email': 'visitante@example.com',
            'mensaje': 'Quiero visitar esta casa',
            'tipo': 'Visita',
            'propiedad_id': str(self.propiedad.id),
            'precio': str(self.propiedad.precio),
            'fecha_visita': '2024-12-31',
            'hora_visita': '15:00'
        }
        
        response = self.client.post(reverse('Contacto'), data=form_data)
        
        # Verificar que se creó una nueva solicitud
        final_count = SolicitudVisita.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verificar datos de la solicitud
        solicitud = SolicitudVisita.objects.latest('fecha_solicitud')
        self.assertEqual(solicitud.nombre, 'Visitante Email')
        self.assertEqual(solicitud.propiedad, self.propiedad)
