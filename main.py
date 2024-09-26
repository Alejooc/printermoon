import wmi
import os
import time
import subprocess
import getpass

# Ruta de la carpeta compartida en red donde se almacenan los PDF
pdf_folder = r"\\192.168.0.164\Compartida"

# Definir una contraseña para el acceso
PASSWORD = "tu_contraseña_secreta"

def solicitar_contraseña():
    """
    Solicita la contraseña al usuario antes de permitir el acceso al archivo bloqueado.
    """
    intentos = 3  # Puedes ajustar el número de intentos permitidos
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

def map_network_drive():
    """
    Mapea la unidad de red Z: a la carpeta compartida en red.
    """
    try:
        # Desmapear cualquier conexión existente a Z:
        subprocess.call(['net', 'use', 'Z:', '/delete'], shell=True)
        # Mapear la unidad Z: a la carpeta compartida
        subprocess.check_call(['net', 'use', 'Z:', r'\\192.168.0.100\unfe\PDF', '/user:usuario', 'contraseña'], shell=True)
        print("Unidad Z: mapeada correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al mapear la unidad de red: {e}")

def set_permissions_deny(file_path):
    """
    Establece permisos para denegar el acceso (lectura, escritura y ejecución) después de que un archivo ha sido impreso.
    """
    try:
        # Comando para denegar permisos a todos los usuarios en el archivo
        subprocess.check_call(['icacls', file_path, '/deny', 'Everyone:(F)'])
        print(f"El archivo {file_path} ha sido bloqueado (se han denegado todos los permisos).")
    except subprocess.CalledProcessError as e:
        print(f"No se pudo cambiar los permisos del archivo {file_path}: {e}")

def desbloquear_archivo(file_path):
    """
    Solicita la contraseña para desbloquear el archivo, si es correcta, restablece los permisos.
    """
    if solicitar_contraseña():
        try:
            # Comando para restablecer permisos a "lectura/escritura"
            subprocess.check_call(['icacls', file_path, '/grant', 'Everyone:F'])
            print(f"El archivo {file_path} ha sido desbloqueado (permisos restaurados).")
        except subprocess.CalledProcessError as e:
            print(f"No se pudo desbloquear el archivo {file_path}: {e}")
    else:
        print("No se puede desbloquear el archivo sin la contraseña correcta.")

def monitor_print_jobs():
    """
    Monitorea los trabajos de impresión y bloquea el archivo PDF después de ser impreso.
    """
    c = wmi.WMI()

    # Monitorea los trabajos de impresión
    print("Monitoreando impresoras...")
    watcher = c.watch_for(
        notification_type="Creation",
        wmi_class="Win32_PrintJob"
    )

    while True:
        try:
            print_job = watcher()

            # Datos del trabajo de impresión
            document_name = print_job.Document
            printer_name = print_job.Name
            user = print_job.Owner

            print(f"Detectado trabajo de impresión: {document_name} en la impresora {printer_name} por el usuario {user}")

            # Verificar si el archivo impreso es un PDF y está en la carpeta monitoreada
            if document_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(pdf_folder, document_name)
                print(f"Buscando archivo en la ruta: {pdf_path}")

                # Imprimir los archivos en la carpeta para verificar si está el archivo
                print("Archivos en la carpeta PDF:")
                print(os.listdir(pdf_folder))

                if os.path.exists(pdf_path):
                    set_permissions_deny(pdf_path)
                else:
                    print(f"El archivo {document_name} no fue encontrado en {pdf_folder}.")
            else:
                print(f"El documento {document_name} no es un archivo PDF.")
        except Exception as e:
            print(f"Error al monitorear trabajos de impresión: {e}")
            time.sleep(5)  # Esperar un poco antes de volver a intentar

if __name__ == "__main__":
    #map_network_drive()  # Descomentar si necesitas mapear la unidad de red antes
    monitor_print_jobs()
