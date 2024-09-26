import wmi
import os
import time
import subprocess
import getpass
import PyPDF2

# Función para cargar la configuración desde el archivo config.txt
def load_config():
    config = {}
    with open('config.txt', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

# Cargar la configuración
config = load_config()
pdf_folder = config.get('pdf_folder', r"\\192.168.0.164\Compartida")
PASSWORD = config.get('PASSWORD', 'tu_contraseña_secreta')

def solicitar_contraseña():
    """Solicita la contraseña al usuario antes de permitir el acceso al archivo bloqueado."""
    intentos = 3
    while intentos > 0:
        password_input = getpass.getpass("Ingrese la contraseña para acceder al archivo: ")
        if password_input == PASSWORD:
            print("Acceso concedido.")
            return True
        else:
            intentos -= 1
            print(f"Contraseña incorrecta. Quedan {intentos} intentos.")
    print("Acceso denegado.")
    return False

def encrypt_pdf(input_pdf_path, output_pdf_path, password):
    """Cifra un archivo PDF y lo guarda con una contraseña."""
    with open(input_pdf_path, 'rb') as input_file:
        reader = PyPDF2.PdfReader(input_file)
        writer = PyPDF2.PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)

def set_permissions_deny(file_path):
    """Establece permisos para denegar el acceso después de que un archivo ha sido impreso."""
    try:
        subprocess.check_call(['icacls', file_path, '/deny', 'Everyone:(F)'])
        print(f"El archivo {file_path} ha sido bloqueado (se han denegado todos los permisos).")
    except subprocess.CalledProcessError as e:
        print(f"No se pudo cambiar los permisos del archivo {file_path}: {e}")

def desbloquear_archivo(file_path):
    """Solicita la contraseña para desbloquear el archivo, si es correcta, restablece los permisos."""
    if solicitar_contraseña():
        try:
            subprocess.check_call(['icacls', file_path, '/grant', 'Everyone:F'])
            print(f"El archivo {file_path} ha sido desbloqueado (permisos restaurados).")
        except subprocess.CalledProcessError as e:
            print(f"No se pudo desbloquear el archivo {file_path}: {e}")
    else:
        print("No se puede desbloquear el archivo sin la contraseña correcta.")

def monitor_print_jobs():
    """Monitorea los trabajos de impresión y bloquea el archivo PDF después de ser impreso."""
    c = wmi.WMI()

    print("Monitoreando impresoras...")
    watcher = c.watch_for(notification_type="Creation", wmi_class="Win32_PrintJob")

    while True:
        try:
            print_job = watcher()

            document_name = print_job.Document
            printer_name = print_job.Name
            user = print_job.Owner

            print(f"Detectado trabajo de impresión: {document_name} en la impresora {printer_name} por el usuario {user}")

            if document_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(pdf_folder, document_name)
                print(f"Buscando archivo en la ruta: {pdf_path}")

                if os.path.exists(pdf_path):
                    
                    output_pdf_path = os.path.join(pdf_folder, f"{document_name}")
                    encrypt_pdf(pdf_path, output_pdf_path, PASSWORD)
                    print(f"Archivo protegido creado: {output_pdf_path}")

                    set_permissions_deny(pdf_path)
                else:
                    print(f"El archivo {document_name} no fue encontrado en {pdf_folder}.")
            else:
                print(f"El documento {document_name} no es un archivo PDF.")
        except Exception as e:
            print(f"Error al monitorear trabajos de impresión: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_print_jobs()
