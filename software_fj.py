"""Software FJ: sistema de gestión de clientes, servicios y reservas.
Programación orientada a objetos con manejo de excepciones y registro en eventos.log.
Para ejecutarlo: python software_fj.py"""

import itertools  # Contador automático de ids
import logging  # Archivo de logs
import re  # Validaciones con expresiones regulares
from abc import ABC, abstractmethod  # Clases y métodos abstractos

# ======================================================================
# 1. EXCEPCIONES PERSONALIZADAS
# ======================================================================
class SoftwareFJError(Exception):
    """Excepción base: todas las demás del sistema heredan de esta."""

    def __init__(self, mensaje, codigo="GENERAL"):
        # Llamamos al constructor de Exception para guardar el mensaje
        super().__init__(mensaje)
        # Guardamos el mensaje para poder usarlo en los logs
        self.mensaje = mensaje
        # Código corto que identifica el tipo de error
        self.codigo = codigo


class ClienteInvalidoError(SoftwareFJError):
    """Se lanza cuando los datos de un cliente no son válidos."""

    def __init__(self, mensaje):
        # Se reutiliza el constructor base con un código propio
        super().__init__(mensaje, codigo="CLIENTE_INVALIDO")


class ServicioInvalidoError(SoftwareFJError):
    """Se lanza cuando un servicio se crea con datos o parámetros inválidos."""

    def __init__(self, mensaje):
        # Código propio para errores de servicios
        super().__init__(mensaje, codigo="SERVICIO_INVALIDO")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando se intenta usar un servicio que no está disponible."""

    def __init__(self, mensaje):
        # Código propio para servicios no disponibles
        super().__init__(mensaje, codigo="SERVICIO_NO_DISPONIBLE")


class CalculoInconsistenteError(SoftwareFJError):
    """Se lanza cuando un cálculo de costos da un resultado incoherente."""

    def __init__(self, mensaje):
        # Código propio para errores de cálculo
        super().__init__(mensaje, codigo="CALCULO_INCONSISTENTE")


class ReservaError(SoftwareFJError):
    """Se lanza en operaciones de reserva no permitidas (la usa la clase Reserva)."""

    def __init__(self, mensaje):
        # Código propio para errores de reservas
        super().__init__(mensaje, codigo="RESERVA_ERROR")


# ======================================================================
# 2. CLASE ABSTRACTA BASE
# ======================================================================
class Entidad(ABC):
    """Representa cualquier entidad general del sistema (cliente, servicio, reserva)."""

    # Contador compartido: cada entidad nueva recibe el siguiente número
    _contador = itertools.count(1)

    def __init__(self):
        # Se asigna un identificador único y automático a la entidad
        self._id = next(Entidad._contador)

    @property
    def id(self):
        # Solo lectura: el id no se puede modificar desde afuera (encapsulación)
        return self._id

    @abstractmethod
    def describir(self):
        """Cada entidad hija debe devolver un texto que la describa."""

    def __str__(self):
        # Al imprimir una entidad se muestra su descripción
        return self.describir()


# ======================================================================
# 3. CLASE CLIENTE
# ======================================================================
# Logger compartido del sistema (la configuración del archivo de logs la hace la simulación)
logger = logging.getLogger("software_fj")

# Solo letras (con tildes y ñ) y espacios
PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$")
# Formato básico de correo: algo@dominio.ext
PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


class Cliente(Entidad):
    """Cliente de Software FJ. Sus datos son privados y se validan al asignarlos."""

    def __init__(self, nombre, documento, correo, telefono):
        # Inicializamos la entidad base (asigna el id)
        super().__init__()
        # Usamos los setters para que cada dato pase por su validación
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono

    # ---------- nombre ----------
    @property
    def nombre(self):
        # Devuelve el nombre guardado
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        # El nombre debe ser texto
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El nombre debe ser un texto.")
        # Quitamos espacios sobrantes al inicio y al final
        valor = valor.strip()
        # Debe tener al menos 3 caracteres y solo letras
        if len(valor) < 3 or not PATRON_NOMBRE.match(valor):
            raise ClienteInvalidoError(f"Nombre inválido: '{valor}'.")
        # Guardamos el nombre ya validado
        self.__nombre = valor

    # ---------- documento ----------
    @property
    def documento(self):
        # Devuelve el documento guardado
        return self.__documento

    @documento.setter
    def documento(self, valor):
        try:
            # Intentamos convertir a número para confirmar que son solo dígitos
            int(str(valor).strip())
        except ValueError as error:
            # Encadenamiento de excepciones: conservamos el error original con "from"
            raise ClienteInvalidoError(f"El documento debe ser numérico: '{valor}'.") from error
        # Texto limpio del documento
        texto = str(valor).strip()
        # Un documento colombiano típico tiene entre 6 y 10 dígitos
        if not texto.isdigit() or not 6 <= len(texto) <= 10:
            raise ClienteInvalidoError(f"El documento debe tener entre 6 y 10 dígitos: '{texto}'.")
        # Guardamos el documento validado
        self.__documento = texto

    # ---------- correo ----------
    @property
    def correo(self):
        # Devuelve el correo guardado
        return self.__correo

    @correo.setter
    def correo(self, valor):
        # Debe ser texto y cumplir el formato de correo
        if not isinstance(valor, str) or not PATRON_CORREO.match(valor.strip()):
            raise ClienteInvalidoError(f"Correo inválido: '{valor}'.")
        # Guardamos el correo en minúsculas
        self.__correo = valor.strip().lower()

    # ---------- teléfono ----------
    @property
    def telefono(self):
        # Devuelve el teléfono guardado
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        # Quitamos espacios para validar solo los dígitos
        texto = str(valor).replace(" ", "")
        # Debe tener solo dígitos y entre 7 y 10 de longitud
        if not texto.isdigit() or not 7 <= len(texto) <= 10:
            raise ClienteInvalidoError(f"Teléfono inválido: '{valor}'.")
        # Guardamos el teléfono validado
        self.__telefono = texto

    # ---------- creación segura ----------
    @classmethod
    def crear(cls, nombre, documento, correo, telefono):
        """Crea un cliente registrando en el log el resultado (try/except/else/finally)."""
        try:
            # Intentamos construir el cliente (aquí se disparan las validaciones)
            cliente = cls(nombre, documento, correo, telefono)
        except ClienteInvalidoError as error:
            # Registramos el error en el log y lo volvemos a lanzar para que lo maneje quien llamó
            logger.error("No se pudo registrar el cliente: %s", error)
            raise
        else:
            # Solo se ejecuta si no hubo errores
            logger.info("Cliente registrado correctamente: %s", cliente.describir())
            return cliente
        finally:
            # Se ejecuta siempre, haya error o no
            logger.debug("Intento de registro de cliente finalizado.")

    def describir(self):
        # Texto con los datos principales del cliente
        return f"Cliente #{self.id}: {self.nombre} (doc. {self.documento}, {self.correo})"


# ======================================================================
# 4. SERVICIOS (ABSTRACTO + 3 HIJOS)
# ======================================================================
# Logger compartido del sistema
logger = logging.getLogger("software_fj")


class Servicio(Entidad):
    """Servicio abstracto de Software FJ. No se puede instanciar directamente."""

    def __init__(self, nombre, tarifa):
        # Inicializamos la entidad base (asigna el id)
        super().__init__()
        # El nombre debe ser un texto no vacío
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El servicio necesita un nombre válido.")
        # La tarifa debe ser un número positivo (bool también es int, por eso se excluye)
        if isinstance(tarifa, bool) or not isinstance(tarifa, (int, float)) or tarifa <= 0:
            raise ServicioInvalidoError(f"Tarifa inválida: '{tarifa}'.")
        # Atributos privados (encapsulación)
        self._nombre = nombre.strip()
        self._tarifa = float(tarifa)
        # Todo servicio nace disponible
        self._disponible = True

    @property
    def nombre(self):
        # Solo lectura
        return self._nombre

    @property
    def tarifa(self):
        # Solo lectura
        return self._tarifa

    @property
    def disponible(self):
        # Indica si el servicio se puede reservar
        return self._disponible

    def activar(self):
        # Marca el servicio como disponible
        self._disponible = True

    def desactivar(self):
        # Marca el servicio como no disponible
        self._disponible = False

    def verificar_disponibilidad(self):
        # Si no está disponible, se lanza la excepción correspondiente
        if not self._disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible.")

    @staticmethod
    def _aplicar_ajustes(base, impuesto, descuento):
        """Aplica descuento e impuesto al costo base y valida que el resultado sea coherente."""
        # El impuesto debe estar entre 0 y 100 %
        if not 0 <= impuesto <= 1:
            raise CalculoInconsistenteError(f"Impuesto fuera de rango (0 a 1): {impuesto}.")
        # El descuento debe estar entre 0 y 100 %
        if not 0 <= descuento <= 1:
            raise CalculoInconsistenteError(f"Descuento fuera de rango (0 a 1): {descuento}.")
        # Primero se descuenta y luego se aplica el impuesto
        total = base * (1 - descuento) * (1 + impuesto)
        # Un costo negativo sería un cálculo inconsistente
        if total < 0:
            raise CalculoInconsistenteError("El costo calculado es negativo.")
        # Redondeamos a 2 decimales
        return round(total, 2)

    # ---------- métodos que cada servicio hijo debe implementar ----------
    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        """Calcula el costo. Los parámetros opcionales dan la sobrecarga:
        calcular_costo(2), calcular_costo(2, 0.19), calcular_costo(2, descuento=0.1)."""

    @abstractmethod
    def validar_parametros(self, duracion, **extras):
        """Valida los parámetros de uso del servicio y lanza ServicioInvalidoError si fallan."""

    # ---------- variantes de cálculo (sobrecarga mediante parámetros opcionales) ----------
    def calcular_costo_con_iva(self, duracion):
        # Variante: solo con IVA del 19 %
        return self.calcular_costo(duracion, impuesto=0.19)

    def calcular_costo_con_descuento(self, duracion, descuento):
        # Variante: solo con descuento, sin impuesto
        return self.calcular_costo(duracion, descuento=descuento)


class ReservaSala(Servicio):
    """Reserva de salas. Duración en horas."""

    def __init__(self, nombre, tarifa_hora, capacidad):
        # Constructor del padre valida nombre y tarifa
        super().__init__(nombre, tarifa_hora)
        # La capacidad debe ser un entero positivo
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError(f"Capacidad inválida: '{capacidad}'.")
        self._capacidad = capacidad

    def validar_parametros(self, duracion, **extras):
        # Las horas deben ser un número entre 1 y 12
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)) or not 1 <= duracion <= 12:
            raise ServicioInvalidoError(f"Las horas de sala deben estar entre 1 y 12: '{duracion}'.")
        # Si se indica el número de personas, no puede superar la capacidad
        personas = extras.get("personas")
        if personas is not None and (not isinstance(personas, int) or not 1 <= personas <= self._capacidad):
            raise ServicioInvalidoError(f"La sala admite máximo {self._capacidad} personas: '{personas}'.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        # Primero se confirma que el servicio esté disponible
        self.verificar_disponibilidad()
        # Se validan las horas
        self.validar_parametros(duracion)
        # Costo base: tarifa por hora multiplicada por las horas
        return self._aplicar_ajustes(self._tarifa * duracion, impuesto, descuento)

    def describir(self):
        # Descripción propia de la sala
        return f"Sala '{self.nombre}' (capacidad {self._capacidad}, ${self.tarifa:,.0f} por hora)"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos. Duración en días."""

    def __init__(self, nombre, tarifa_dia, equipo, unidades):
        # Constructor del padre valida nombre y tarifa
        super().__init__(nombre, tarifa_dia)
        # El tipo de equipo debe ser texto no vacío
        if not isinstance(equipo, str) or not equipo.strip():
            raise ServicioInvalidoError("Debe indicar el equipo a alquilar.")
        # Las unidades deben ser un entero positivo
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades <= 0:
            raise ServicioInvalidoError(f"Unidades inválidas: '{unidades}'.")
        self._equipo = equipo.strip()
        self._unidades = unidades

    def validar_parametros(self, duracion, **extras):
        # Los días deben ser un entero entre 1 y 30
        if isinstance(duracion, bool) or not isinstance(duracion, int) or not 1 <= duracion <= 30:
            raise ServicioInvalidoError(f"Los días de alquiler deben estar entre 1 y 30: '{duracion}'.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        # Se confirma disponibilidad
        self.verificar_disponibilidad()
        # Se validan los días
        self.validar_parametros(duracion)
        # Costo base: tarifa por día más un 5 % fijo de seguro del equipo
        base = self._tarifa * duracion * 1.05
        return self._aplicar_ajustes(base, impuesto, descuento)

    def describir(self):
        # Descripción propia del alquiler
        return f"Alquiler de {self._equipo} '{self.nombre}' ({self._unidades} unid., ${self.tarifa:,.0f} por día)"


class AsesoriaEspecializada(Servicio):
    """Asesoría especializada. Duración en horas; la tarifa depende del nivel del asesor."""

    # Multiplicador de la tarifa según el nivel
    NIVELES = {"junior": 1.0, "senior": 1.5}

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="junior"):
        # Constructor del padre valida nombre y tarifa
        super().__init__(nombre, tarifa_hora)
        # La especialidad debe ser texto no vacío
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ServicioInvalidoError("Debe indicar la especialidad de la asesoría.")
        # El nivel debe existir en el diccionario de niveles
        if not isinstance(nivel, str) or nivel.lower() not in self.NIVELES:
            raise ServicioInvalidoError(f"Nivel inválido (use junior o senior): '{nivel}'.")
        self._especialidad = especialidad.strip()
        self._nivel = nivel.lower()

    def validar_parametros(self, duracion, **extras):
        # Las horas deben ser un número entre 1 y 8
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)) or not 1 <= duracion <= 8:
            raise ServicioInvalidoError(f"Las horas de asesoría deben estar entre 1 y 8: '{duracion}'.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        # Se confirma disponibilidad
        self.verificar_disponibilidad()
        # Se validan las horas
        self.validar_parametros(duracion)
        # Costo base: tarifa por hora, horas y multiplicador del nivel
        base = self._tarifa * duracion * self.NIVELES[self._nivel]
        return self._aplicar_ajustes(base, impuesto, descuento)

    def describir(self):
        # Descripción propia de la asesoría
        return f"Asesoría '{self.nombre}' de {self._especialidad} (nivel {self._nivel}, ${self.tarifa:,.0f} por hora)"


# ======================================================================
# 5. CLASE RESERVA
# ======================================================================
# Logger compartido del sistema
logger = logging.getLogger("software_fj")

# Porcentaje de IVA aplicado al confirmar una reserva
IVA = 0.19


class Reserva(Entidad):
    """Reserva de un servicio por parte de un cliente. Estados: pendiente, confirmada, procesada, cancelada."""

    def __init__(self, cliente, servicio, duracion, **extras):
        # Inicializamos la entidad base (asigna el id)
        super().__init__()
        # El cliente debe ser un objeto Cliente
        if not isinstance(cliente, Cliente):
            raise ReservaError("La reserva necesita un cliente válido.")
        # El servicio debe ser un objeto Servicio
        if not isinstance(servicio, Servicio):
            raise ReservaError("La reserva necesita un servicio válido.")
        try:
            # El propio servicio valida la duración y los datos extra (personas, etc.)
            servicio.validar_parametros(duracion, **extras)
        except ServicioInvalidoError as error:
            # Encadenamiento: el error original queda guardado como causa
            raise ReservaError(f"Parámetros de reserva inválidos: {error}") from error
        # Guardamos los datos de la reserva (privados)
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._estado = "pendiente"
        self._costo = None

    @property
    def estado(self):
        # Solo lectura: el estado cambia únicamente con los métodos de la clase
        return self._estado

    @property
    def costo(self):
        # Solo lectura: se calcula al confirmar
        return self._costo

    def confirmar(self):
        """Confirma la reserva y calcula su costo con IVA."""
        # Solo se puede confirmar una reserva pendiente
        if self._estado != "pendiente":
            raise ReservaError(f"No se puede confirmar una reserva en estado '{self._estado}'.")
        try:
            # El servicio calcula el costo (puede fallar si no está disponible)
            costo = self._servicio.calcular_costo(self._duracion, impuesto=IVA)
        except (ServicioNoDisponibleError, CalculoInconsistenteError) as error:
            # Encadenamos el error del servicio dentro de un error de reserva
            logger.error("Reserva #%s no confirmada: %s", self.id, error)
            raise ReservaError(f"No se pudo confirmar la reserva #{self.id}: {error}") from error
        else:
            # Solo si no hubo error se guarda el costo y cambia el estado
            self._costo = costo
            self._estado = "confirmada"
            logger.info("Reserva #%s confirmada. Costo con IVA: $%s", self.id, f"{costo:,.0f}")
        finally:
            # Se ejecuta siempre
            logger.debug("Intento de confirmación de la reserva #%s finalizado.", self.id)

    def cancelar(self):
        """Cancela la reserva si aún no fue procesada ni cancelada."""
        # No se puede cancelar algo ya procesado o ya cancelado
        if self._estado in ("procesada", "cancelada"):
            raise ReservaError(f"No se puede cancelar una reserva en estado '{self._estado}'.")
        # Cambiamos el estado
        self._estado = "cancelada"
        logger.info("Reserva #%s cancelada.", self.id)

    def procesar(self):
        """Procesa una reserva confirmada (ejecuta el servicio)."""
        # Solo se procesa una reserva confirmada
        if self._estado != "confirmada":
            raise ReservaError(f"Solo se procesa una reserva confirmada (estado actual: '{self._estado}').")
        # Cambiamos el estado
        self._estado = "procesada"
        logger.info("Reserva #%s procesada.", self.id)

    def describir(self):
        # Resumen de la reserva
        costo = f"${self._costo:,.0f}" if self._costo is not None else "sin calcular"
        return f"Reserva #{self.id} [{self._estado}]: {self._cliente.nombre} -> {self._servicio.nombre} ({self._duracion}), costo {costo}"


# ======================================================================
# 6. PROGRAMA PRINCIPAL (SIMULACIÓN)
# ======================================================================
# ---------- configuración del log: archivo + pantalla ----------
logger = logging.getLogger("software_fj")  # Mismo nombre que usan las demás clases
logger.setLevel(logging.DEBUG)  # Se registra todo, desde DEBUG hacia arriba
formato = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")  # Formato de cada línea
archivo = logging.FileHandler("eventos.log", mode="w", encoding="utf-8")  # Archivo de logs
archivo.setFormatter(formato)
logger.addHandler(archivo)
pantalla = logging.StreamHandler()  # También se muestra en consola
pantalla.setLevel(logging.INFO)
pantalla.setFormatter(formato)
logger.addHandler(pantalla)


def ejecutar(numero, titulo, accion):
    """Ejecuta una operación; si falla, registra el error y el programa sigue."""
    print(f"\n--- Operación {numero}: {titulo} ---")
    try:
        # Se ejecuta la operación y se muestra su resultado
        resultado = accion()
        print("   Resultado:", resultado)
        return resultado
    except SoftwareFJError as error:
        # Error controlado del sistema
        logger.error("[%s] %s", error.codigo, error)
        if error.__cause__:
            logger.error("   causa original: %r", error.__cause__)
    except Exception as error:  # Cualquier otro error inesperado (ej. TypeError)
        logger.error("[ERROR INESPERADO] %s: %s", type(error).__name__, error)
    return None


def main():
    # Estas variables guardan los objetos creados para usarlos en operaciones posteriores
    print("=== SOFTWARE FJ: simulación ===")

    # --- Clientes ---
    c1 = ejecutar(1, "Cliente válido", lambda: Cliente.crear("Efraín Castellares", "1012345678", "efrain@correo.com", "3246857556"))
    c2 = ejecutar(2, "Cliente válido", lambda: Cliente.crear("Laura Gómez", "52123456", "laura@correo.com", "3001234567"))
    ejecutar(3, "Cliente inválido (correo mal escrito)", lambda: Cliente.crear("Pedro Ruiz", "79123456", "pedro-correo", "3101234567"))
    ejecutar(4, "Cliente inválido (documento con letras)", lambda: Cliente.crear("Ana Soto", "ABC123", "ana@correo.com", "3201234567"))

    # --- Servicios ---
    sala = ejecutar(5, "Servicio válido: sala", lambda: ReservaSala("Sala Ejecutiva", 50000, 10))
    equipo = ejecutar(6, "Servicio válido: equipo", lambda: AlquilerEquipo("Portátil Pro", 30000, "Laptop", 5))
    asesoria = ejecutar(7, "Servicio válido: asesoría", lambda: AsesoriaEspecializada("Redes Cisco", 80000, "Redes", "senior"))
    ejecutar(8, "Servicio inválido (tarifa negativa)", lambda: ReservaSala("Sala Rota", -100, 5))
    ejecutar(9, "Instanciar la clase abstracta Servicio", lambda: Servicio("X", 1000))

    # --- Polimorfismo: el mismo método calcular_costo con tres servicios distintos ---
    print("\n--- Polimorfismo: costo de 2 unidades en cada servicio ---")
    for servicio in (sala, equipo, asesoria):
        print("  ", servicio.describir(), "->", servicio.calcular_costo(2))

    # --- Reservas ---
    r1 = ejecutar(10, "Reserva exitosa (sala 3 horas)", lambda: Reserva(c1, sala, 3, personas=6))
    ejecutar(11, "Confirmar reserva 1", lambda: r1.confirmar() or r1.describir())
    r2 = ejecutar(12, "Reserva exitosa (equipo 5 días)", lambda: Reserva(c2, equipo, 5))
    ejecutar(13, "Confirmar reserva 2", lambda: r2.confirmar() or r2.describir())
    ejecutar(14, "Reserva fallida (20 horas de sala)", lambda: Reserva(c1, sala, 20))
    ejecutar(15, "Reserva fallida (sin cliente)", lambda: Reserva(None, sala, 2))
    ejecutar(16, "Procesar reserva 1", lambda: r1.procesar() or r1.describir())
    ejecutar(17, "Cancelar reserva ya procesada (falla)", lambda: r1.cancelar())
    asesoria.desactivar()  # Dejamos la asesoría no disponible
    r3 = ejecutar(18, "Reserva de asesoría", lambda: Reserva(c2, asesoria, 2))
    ejecutar(19, "Confirmar con servicio no disponible (falla)", lambda: r3.confirmar())
    ejecutar(20, "Cancelar reserva 3", lambda: r3.cancelar() or r3.describir())

    print("\n=== Simulación terminada: el programa nunca se detuvo. Revisa eventos.log ===")


# Solo se ejecuta si corremos este archivo directamente
if __name__ == "__main__":
    main()
