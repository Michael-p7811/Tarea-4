"""Jerarquía de excepciones del dominio para Software FJ."""


class SoftwareFJError(Exception):
    """Excepción base del sistema Software FJ."""

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ValidacionError(SoftwareFJError):
    """Error por datos inválidos, formatos incorrectos o parámetros faltantes."""


class DisponibilidadError(SoftwareFJError):
    """Error cuando un servicio o recurso no está disponible."""


class CalculoError(SoftwareFJError):
    """Error durante cálculos financieros, tarifas, impuestos o descuentos."""


class ReservaError(SoftwareFJError):
    """Error en el ciclo de vida, estado o procesamiento de una reserva."""

"""Configuración y utilidades de registro en archivo para Software FJ."""

from __future__ import annotations

import logging
from pathlib import Path


def configurar_logger(log_path: str = "logs/software_fj.log") -> logging.Logger:
    """Crea y devuelve un logger que escribe eventos y errores en archivo y consola."""
    ruta = Path(log_path)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.DEBUG)

    # Evita duplicar handlers si se reconfigura en pruebas
    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(ruta, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formato)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formato)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

"""Entidades base y gestión encapsulada de clientes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import re

from src.exceptions import ValidacionError


class EntidadBase(ABC):
    """Clase abstracta que representa entidades generales del sistema."""

    def __init__(self, entidad_id: str) -> None:
        if not isinstance(entidad_id, str) or not entidad_id.strip():
            raise ValidacionError(
                "El identificador de la entidad es obligatorio y debe ser un texto no vacío.",
                context={"entidad_id": entidad_id},
            )
        self._id: str = entidad_id.strip().upper()
        self._creado_en: datetime = datetime.now()
        self._activo: bool = True

    @property
    def id(self) -> str:
        return self._id

    @property
    def creado_en(self) -> datetime:
        return self._creado_en

    @property
    def activo(self) -> bool:
        return self._activo

    def desactivar(self) -> None:
        self._activo = False

    def activar(self) -> None:
        self._activo = True

    @abstractmethod
    def resumen(self) -> str:
        """Devuelve una representación resumida de la entidad."""


class Cliente(EntidadBase):
    """Representa un cliente de Software FJ con encapsulación y validaciones estrictas."""

    _EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(
        self,
        cliente_id: str,
        nombre: str,
        correo: str,
        documento: str,
        empresa: str | None = None,
    ) -> None:
        super().__init__(cliente_id)
        self.nombre = nombre
        self.correo = correo
        self.documento = documento
        self.empresa = empresa

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise ValidacionError(
                "El nombre del cliente debe tener al menos 2 caracteres.",
                context={"cliente_id": self._id, "nombre": valor},
            )
        self._nombre = valor.strip()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if not isinstance(valor, str) or not self._EMAIL_REGEX.match(valor.strip()):
            raise ValidacionError(
                "El correo electrónico del cliente no tiene un formato válido.",
                context={"cliente_id": self._id, "correo": valor},
            )
        self._correo = valor.strip().lower()

    @property
    def documento(self) -> str:
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 5:
            raise ValidacionError(
                "El documento de identidad o NIT debe tener al menos 5 caracteres.",
                context={"cliente_id": self._id, "documento": valor},
            )
        self._documento = valor.strip()

    @property
    def empresa(self) -> str | None:
        return self._empresa

    @empresa.setter
    def empresa(self, valor: str | None) -> None:
        if valor is not None and not isinstance(valor, str):
            raise ValidacionError(
                "El nombre de la empresa debe ser texto o None.",
                context={"cliente_id": self._id, "empresa": valor},
            )
        self._empresa = valor.strip() if isinstance(valor, str) and valor.strip() else None

    def resumen(self) -> str:
        org = f" ({self._empresa})" if self._empresa else ""
        return f"Cliente [{self._id}] {self._nombre}{org} - {self._correo}"

"""Catálogo polimórfico de servicios de Software FJ."""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import singledispatchmethod

from src.entities import EntidadBase
from src.exceptions import CalculoError, DisponibilidadError, ValidacionError


class Servicio(EntidadBase, ABC):
    """Clase abstracta base para los servicios ofrecidos por Software FJ."""

    def __init__(
        self,
        servicio_id: str,
        nombre: str,
        tarifa_base: float,
        disponible: bool = True,
    ) -> None:
        super().__init__(servicio_id)
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidacionError(
                "El nombre del servicio es obligatorio.",
                context={"servicio_id": servicio_id, "nombre": nombre},
            )
        try:
            tarifa_num = float(tarifa_base)
        except (TypeError, ValueError) as exc:
            raise CalculoError(
                "La tarifa base debe ser un valor numérico válido.",
                context={"servicio_id": servicio_id, "tarifa_base": tarifa_base},
            ) from exc

        if tarifa_num <= 0:
            raise ValidacionError(
                "La tarifa base del servicio debe ser mayor que cero.",
                context={"servicio_id": servicio_id, "tarifa_base": tarifa_num},
            )

        self._nombre: str = nombre.strip()
        self._tarifa_base: float = tarifa_num
        self._disponible: bool = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    def verificar_disponibilidad(self) -> None:
        if not self._activo or not self._disponible:
            raise DisponibilidadError(
                f"El servicio '{self._nombre}' ({self._id}) no está disponible.",
                context={"servicio_id": self._id, "disponible": self._disponible, "activo": self._activo},
            )

    @abstractmethod
    def validar_parametros(self, cantidad: float) -> None:
        """Valida duración, unidades u horas requeridas por el servicio."""

    @abstractmethod
    def _subtotal_por_cantidad(self, cantidad: float) -> float:
        """Calcula el subtotal antes de descuentos o impuestos."""

    @abstractmethod
    def describir(self) -> str:
        """Describe las características específicas del servicio."""

    def resumen(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return f"{self.describir()} | Tarifa base: ${self._tarifa_base:,.2f} | {estado}"

    def calcular_costo(
        self,
        cantidad: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ) -> float:
        """Calcula el costo total con soporte para descuento e impuesto opcionales."""
        self.validar_parametros(cantidad)
        try:
            cant = float(cantidad)
            desc = float(descuento_pct)
            imp = float(impuesto_pct)
        except (TypeError, ValueError) as exc:
            raise CalculoError(
                "Los parámetros numéricos para el cálculo de costo no son válidos.",
                context={
                    "servicio_id": self._id,
                    "cantidad": cantidad,
                    "descuento_pct": descuento_pct,
                    "impuesto_pct": impuesto_pct,
                },
            ) from exc

        if not (0.0 <= desc < 100.0):
            raise CalculoError(
                "El porcentaje de descuento debe estar entre 0 y menor a 100.",
                context={"servicio_id": self._id, "descuento_pct": desc},
            )
        if imp < 0.0:
            raise CalculoError(
                "El porcentaje de impuesto no puede ser negativo.",
                context={"servicio_id": self._id, "impuesto_pct": imp},
            )

        try:
            subtotal = self._subtotal_por_cantidad(cant)
            con_descuento = subtotal * (1.0 - desc / 100.0)
            total = con_descuento * (1.0 + imp / 100.0)
            if total < 0:
                raise CalculoError("El total calculado no puede ser negativo.")
            return round(total, 2)
        except ZeroDivisionError as exc:
            raise CalculoError(
                "División por cero durante el cálculo del costo.",
                context={"servicio_id": self._id, "cantidad": cant},
            ) from exc
        except SoftwareFJError:
            raise
        except Exception as exc:
            raise CalculoError(
                "Error inesperado al calcular el costo del servicio.",
                context={"servicio_id": self._id, "cantidad": cant},
            ) from exc

    @singledispatchmethod
    def calcular_costo_sobrecargado(self, ajuste: object, cantidad: float = 1.0) -> float:
        """Sobrecarga polimórfica según el tipo del parámetro de ajuste."""
        raise CalculoError(
            f"Tipo de ajuste no soportado para calcular_costo_sobrecargado: {type(ajuste).__name__}",
            context={"servicio_id": self._id, "tipo_ajuste": type(ajuste).__name__},
        )

    @calcular_costo_sobrecargado.register
    def _(self, ajuste: (int, float), cantidad: float = 1.0) -> float:
        """Ajuste numérico interpretado como porcentaje de impuesto (ej. 19 -> 19%)."""
        return self.calcular_costo(cantidad=cantidad, descuento_pct=0.0, impuesto_pct=float(ajuste))

    @calcular_costo_sobrecargado.register
    def _(self, ajuste: dict, cantidad: float = 1.0) -> float:
        """Ajuste mediante diccionario con claves opcionales 'descuento_pct' e 'impuesto_pct'."""
        return self.calcular_costo(
            cantidad=cantidad,
            descuento_pct=ajuste.get("descuento_pct", 0.0),
            impuesto_pct=ajuste.get("impuesto_pct", 0.0),
        )


class ReservaSala(Servicio):
    """Servicio de reserva de salas de reuniones o capacitación (por horas)."""

    def __init__(
        self,
        servicio_id: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_personas: int,
        disponible: bool = True,
    ) -> None:
        super().__init__(servicio_id, nombre, tarifa_hora, disponible)
        if not isinstance(capacidad_personas, int) or capacidad_personas <= 0:
            raise ValidacionError(
                "La capacidad de la sala debe ser un entero mayor que cero.",
                context={"servicio_id": servicio_id, "capacidad_personas": capacidad_personas},
            )
        self._capacidad_personas = capacidad_personas

    @property
    def capacidad_personas(self) -> int:
        return self._capacidad_personas

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, (int, float)) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValidacionError(
                "La duración de reserva de sala debe ser un número de horas mayor que cero.",
                context={"servicio_id": self._id, "horas": cantidad},
            )

    def _subtotal_por_cantidad(self, cantidad: float) -> float:
        return self._tarifa_base * cantidad

    def describir(self) -> str:
        return f"Reserva de Sala [{self._id}] '{self._nombre}' (Capacidad: {self._capacidad_personas} personas)"


class AlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos tecnológicos (por días)."""

    def __init__(
        self,
        servicio_id: str,
        nombre: str,
        tarifa_dia: float,
        especificaciones: str,
        disponible: bool = True,
    ) -> None:
        super().__init__(servicio_id, nombre, tarifa_dia, disponible)
        if not isinstance(especificaciones, str) or not especificaciones.strip():
            raise ValidacionError(
                "Las especificaciones del equipo son obligatorias.",
                context={"servicio_id": servicio_id, "especificaciones": especificaciones},
            )
        self._especificaciones = especificaciones.strip()

    @property
    def especificaciones(self) -> str:
        return self._especificaciones

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValidacionError(
                "El alquiler de equipos requiere un número entero de días mayor que cero.",
                context={"servicio_id": self._id, "dias": cantidad},
            )

    def _subtotal_por_cantidad(self, cantidad: float) -> float:
        # Cargo fijo logístico del 5% por preparación y entrega del equipo
        return (self._tarifa_base * cantidad) * 1.05

    def describir(self) -> str:
        return f"Alquiler de Equipo [{self._id}] '{self._nombre}' ({self._especificaciones})"


class AsesoriaEspecializada(Servicio):
    """Servicio de consultoría o asesoría técnica especializada (por sesiones/horas)."""

    def __init__(
        self,
        servicio_id: str,
        nombre: str,
        tarifa_sesion: float,
        especialidad: str,
        disponible: bool = True,
    ) -> None:
        super().__init__(servicio_id, nombre, tarifa_sesion, disponible)
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ValidacionError(
                "La especialidad de la asesoría es obligatoria.",
                context={"servicio_id": servicio_id, "especialidad": especialidad},
            )
        self._especialidad = especialidad.strip()

    @property
    def especialidad(self) -> str:
        return self._especialidad

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, (int, float)) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValidacionError(
                "La cantidad de sesiones/horas de asesoría debe ser mayor que cero.",
                context={"servicio_id": self._id, "cantidad": cantidad},
            )

    def _subtotal_por_cantidad(self, cantidad: float) -> float:
        return self._tarifa_base * cantidad

    def describir(self) -> str:
        return f"Asesoría Especializada [{self._id}] '{self._nombre}' (Área: {self._especialidad})"

"""Gestión de reservas de servicios para clientes en Software FJ."""

from __future__ import annotations

from src.entities import Cliente, EntidadBase
from src.exceptions import ReservaError, SoftwareFJError, ValidacionError
from src.services import Servicio


class Reserva(EntidadBase):
    """Integra un cliente, un servicio, duración/cantidad y su ciclo de estados."""

    ESTADOS_VALIDOS = {"PENDIENTE", "CONFIRMADA", "CANCELADA"}

    def __init__(
        self,
        reserva_id: str,
        cliente: Cliente,
        servicio: Servicio,
        cantidad: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ) -> None:
        super().__init__(reserva_id)

        if not isinstance(cliente, Cliente):
            raise ValidacionError(
                "La reserva requiere una instancia válida de Cliente.",
                context={"reserva_id": reserva_id, "cliente": cliente},
            )
        if not isinstance(servicio, Servicio):
            raise ValidacionError(
                "La reserva requiere una instancia válida de Servicio.",
                context={"reserva_id": reserva_id, "servicio": servicio},
            )
        if not cliente.activo:
            raise ReservaError(
                f"No se puede crear una reserva para el cliente inactivo '{cliente.id}'.",
                context={"reserva_id": reserva_id, "cliente_id": cliente.id},
            )

        servicio.verificar_disponibilidad()
        servicio.validar_parametros(cantidad)

        self._cliente: Cliente = cliente
        self._servicio: Servicio = servicio
        self._cantidad: float = cantidad
        self._descuento_pct: float = descuento_pct
        self._impuesto_pct: float = impuesto_pct
        self._estado: str = "PENDIENTE"
        self._costo_total: float = servicio.calcular_costo(
            cantidad=cantidad,
            descuento_pct=descuento_pct,
            impuesto_pct=impuesto_pct,
        )

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def cantidad(self) -> float:
        return self._cantidad

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def confirmar(self) -> None:
        if self._estado == "CANCELADA":
            raise ReservaError(
                f"No se puede confirmar la reserva '{self._id}' porque está cancelada.",
                context={"reserva_id": self._id, "estado": self._estado},
            )
        if self._estado == "CONFIRMADA":
            raise ReservaError(
                f"La reserva '{self._id}' ya se encuentra confirmada.",
                context={"reserva_id": self._id, "estado": self._estado},
            )
        self._servicio.verificar_disponibilidad()
        self._estado = "CONFIRMADA"

    def cancelar(self) -> None:
        if self._estado == "CANCELADA":
            raise ReservaError(
                f"La reserva '{self._id}' ya fue cancelada previamente.",
                context={"reserva_id": self._id, "estado": self._estado},
            )
        self._estado = "CANCELADA"

    def procesar(self) -> float:
        """Procesa y confirma la reserva asegurando disponibilidad y cálculo vigente."""
        try:
            self._servicio.verificar_disponibilidad()
            self._costo_total = self._servicio.calcular_costo(
                cantidad=self._cantidad,
                descuento_pct=self._descuento_pct,
                impuesto_pct=self._impuesto_pct,
            )
            if self._estado == "PENDIENTE":
                self.confirmar()
            elif self._estado != "CONFIRMADA":
                raise ReservaError(
                    f"Estado '{self._estado}' no procesable para la reserva '{self._id}'.",
                    context={"reserva_id": self._id, "estado": self._estado},
                )
            return self._costo_total
        except SoftwareFJError as exc:
            raise ReservaError(
                f"Fallo al procesar la reserva '{self._id}': {exc.message}",
                context={"reserva_id": self._id, "estado": self._estado},
            ) from exc

    def resumen(self) -> str:
        return (
            f"Reserva [{self._id}] | Estado: {self._estado} | "
            f"Cliente: {self._cliente.nombre} ({self._cliente.id}) | "
            f"Servicio: {self._servicio.nombre} ({self._servicio.id}) | "
            f"Cantidad: {self._cantidad} | Total: ${self._costo_total:,.2f}"
        )

"""Gestor central en memoria para Software FJ (sin base de datos)."""

from __future__ import annotations

import logging

from src.booking import Reserva
from src.entities import Cliente
from src.exceptions import ReservaError, SoftwareFJError, ValidacionError
from src.services import Servicio


class SistemaSoftwareFJ:
    """Administra clientes, servicios y reservas en memoria con registro en log."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def _buscar_cliente(self, cliente_id: str) -> Cliente:
        for cliente in self.clientes:
            if cliente.id == cliente_id.strip().upper():
                return cliente
        raise ValidacionError(
            f"No existe un cliente registrado con ID '{cliente_id}'.",
            context={"cliente_id": cliente_id},
        )

    def _buscar_servicio(self, servicio_id: str) -> Servicio:
        for servicio in self.servicios:
            if servicio.id == servicio_id.strip().upper():
                return servicio
        raise ValidacionError(
            f"No existe un servicio registrado con ID '{servicio_id}'.",
            context={"servicio_id": servicio_id},
        )

    def _buscar_reserva(self, reserva_id: str) -> Reserva:
        for reserva in self.reservas:
            if reserva.id == reserva_id.strip().upper():
                return reserva
        raise ReservaError(
            f"No existe una reserva con ID '{reserva_id}'.",
            context={"reserva_id": reserva_id},
        )

    def registrar_cliente(
        self,
        cliente_id: str,
        nombre: str,
        correo: str,
        documento: str,
        empresa: str | None = None,
    ) -> Cliente | None:
        try:
            if any(c.id == cliente_id.strip().upper() for c in self.clientes):
                raise ValidacionError(
                    f"Ya existe un cliente con el ID '{cliente_id}'.",
                    context={"cliente_id": cliente_id},
                )
            cliente = Cliente(cliente_id, nombre, correo, documento, empresa)
        except SoftwareFJError as exc:
            self.logger.error("Error al registrar cliente | %s | ctx=%s", exc.message, exc.context)
            return None
        else:
            self.clientes.append(cliente)
            self.logger.info("Cliente registrado correctamente: %s", cliente.resumen())
            return cliente
        finally:
            self.logger.debug("Finalizó intento de registro de cliente (ID=%s).", cliente_id)

    def registrar_servicio(self, servicio: Servicio | None) -> Servicio | None:
        try:
            if not isinstance(servicio, Servicio):
                raise ValidacionError(
                    "El objeto proporcionado no es una instancia válida de Servicio.",
                    context={"servicio": servicio},
                )
            if any(s.id == servicio.id for s in self.servicios):
                raise ValidacionError(
                    f"Ya existe un servicio registrado con el ID '{servicio.id}'.",
                    context={"servicio_id": servicio.id},
                )
        except SoftwareFJError as exc:
            self.logger.error("Error al registrar servicio | %s | ctx=%s", exc.message, exc.context)
            return None
        else:
            self.servicios.append(servicio)
            self.logger.info("Servicio registrado correctamente: %s", servicio.resumen())
            return servicio
        finally:
            sid = servicio.id if isinstance(servicio, Servicio) else "N/A"
            self.logger.debug("Finalizó intento de registro de servicio (ID=%s).", sid)

    def crear_y_procesar_reserva(
        self,
        reserva_id: str,
        cliente_id: str,
        servicio_id: str,
        cantidad: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ) -> Reserva | None:
        try:
            if any(r.id == reserva_id.strip().upper() for r in self.reservas):
                raise ReservaError(
                    f"Ya existe una reserva con el ID '{reserva_id}'.",
                    context={"reserva_id": reserva_id},
                )
            cliente = self._buscar_cliente(cliente_id)
            servicio = self._buscar_servicio(servicio_id)
            reserva = Reserva(
                reserva_id=reserva_id,
                cliente=cliente,
                servicio=servicio,
                cantidad=cantidad,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
            )
            reserva.procesar()
        except SoftwareFJError as exc:
            self.logger.error("Error en reserva '%s' | %s | ctx=%s", reserva_id, exc.message, exc.context)
            return None
        else:
            self.reservas.append(reserva)
            self.logger.info("Reserva procesada con éxito: %s", reserva.resumen())
            return reserva
        finally:
            self.logger.debug("Finalizó operación de reserva (ID=%s).", reserva_id)

    def cancelar_reserva(self, reserva_id: str) -> bool:
        try:
            reserva = self._buscar_reserva(reserva_id)
            reserva.cancelar()
        except SoftwareFJError as exc:
            self.logger.error("No se pudo cancelar la reserva '%s' | %s", reserva_id, exc.message)
            return False
        else:
            self.logger.info("Reserva cancelada: %s", reserva.resumen())
            return True
        finally:
            self.logger.debug("Finalizó intento de cancelación de reserva (ID=%s).", reserva_id)

"""Punto de entrada y simulación de 12 operaciones para Software FJ."""

from __future__ import annotations

from src.exceptions import SoftwareFJError
from src.logger import configurar_logger
from src.services import AlquilerEquipo, AsesoriaEspecializada, ReservaSala
from src.system import SistemaSoftwareFJ


def construir_servicio_seguro(logger, creador_fn, etiqueta: str):
    """Envuelve la construcción de un servicio para capturar y encadenar errores."""
    try:
        servicio = creador_fn()
    except SoftwareFJError as exc:
        logger.error("Fallo construyendo %s | %s | ctx=%s", etiqueta, exc.message, exc.context)
        return None
    else:
        return servicio


def ejecutar_simulacion() -> None:
    logger = configurar_logger("logs/software_fj.log")
    sistema = SistemaSoftwareFJ(logger=logger)
    logger.info("=== INICIO DE SIMULACIÓN SOFTWARE FJ ===")

    # 1. Registro válido de cliente
    sistema.registrar_cliente("CLI-01", "Laura Gómez", "laura@empresa.com", "10203040", "TechAndes")

    # 2. Registro inválido de cliente (correo mal formado)
    sistema.registrar_cliente("CLI-02", "Carlos Ruiz", "correo-invalido", "900123456")

    # 3. Registro válido de segundo cliente
    sistema.registrar_cliente("CLI-03", "Andrés Pérez", "andres@consultora.co", "71829304")

    # 4. Creación y registro válido de servicio: Reserva de Sala
    sala = construir_servicio_seguro(
        logger,
        lambda: ReservaSala("SRV-SALA-1", "Sala Ejecutiva A", tarifa_hora=80.0, capacidad_personas=12),
        "ReservaSala",
    )
    sistema.registrar_servicio(sala)

    # 5. Creación y registro válido de servicio: Alquiler de Equipo
    equipo = construir_servicio_seguro(
        logger,
        lambda: AlquilerEquipo("SRV-EQ-1", "Laptop Workstation", tarifa_dia=45.0, especificaciones="32GB RAM / 1TB SSD"),
        "AlquilerEquipo",
    )
    sistema.registrar_servicio(equipo)

    # 6. Creación y registro válido de servicio: Asesoría Especializada
    asesoria = construir_servicio_seguro(
        logger,
        lambda: AsesoriaEspecializada("SRV-ASE-1", "Arquitectura Cloud", tarifa_sesion=150.0, especialidad="AWS / DevOps"),
        "AsesoriaEspecializada",
    )
    sistema.registrar_servicio(asesoria)

    # 7. Creación inválida de servicio (tarifa no numérica -> encadena CalculoError desde ValueError)
    servicio_invalido = construir_servicio_seguro(
        logger,
        lambda: ReservaSala("SRV-SALA-ERR", "Sala Rota", tarifa_hora="no_es_numero", capacidad_personas=6),  # type: ignore[arg-type]
        "ReservaSala inválida",
    )
    sistema.registrar_servicio(servicio_invalido)

    # 8. Uso de sobrecarga de métodos para calcular costos (diccionario vs. impuesto numérico)
    if asesoria is not None:
        costo_con_dict = asesoria.calcular_costo_sobrecargado({"descuento_pct": 10.0, "impuesto_pct": 19.0}, cantidad=2)
        costo_con_iva = asesoria.calcular_costo_sobrecargado(19, cantidad=2)
        logger.info("Cálculo sobrecargado (dict desc+IVA): $%.2f | (IVA 19%%): $%.2f", costo_con_dict, costo_con_iva)

    # 9. Reserva exitosa de sala para CLI-01 (3 horas, 5% descuento, 19% impuesto)
    sistema.crear_y_procesar_reserva("RES-01", "CLI-01", "SRV-SALA-1", cantidad=3, descuento_pct=5.0, impuesto_pct=19.0)

    # 10. Reserva exitosa de asesoría para CLI-03
    sistema.crear_y_procesar_reserva("RES-02", "CLI-03", "SRV-ASE-1", cantidad=2, descuento_pct=0.0, impuesto_pct=19.0)

    # 11. Reserva fallida: cliente inexistente (CLI-02 falló en el paso 2)
    sistema.crear_y_procesar_reserva("RES-03", "CLI-02", "SRV-EQ-1", cantidad=2)

    # 12. Reserva fallida: servicio no disponible (alquiler de equipo con cantidad decimal inválida o no disponible)
    if equipo is not None:
        equipo.disponible = False
    sistema.crear_y_procesar_reserva("RES-04", "CLI-01", "SRV-EQ-1", cantidad=2)

    logger.info("=== RESUMEN FINAL EN MEMORIA ===")
    logger.info(
        "Clientes: %d | Servicios: %d | Reservas: %d",
        len(sistema.clientes),
        len(sistema.servicios),
        len(sistema.reservas),
    )
    for res in sistema.reservas:
        logger.info(" - %s", res.resumen())

    logger.info("=== FIN DE SIMULACIÓN SOFTWARE FJ ===")
    print(f"Simulación completada. Revisa el archivo de log en: logs/software_fj.log")
    print(f"Total registrados -> Clientes: {len(sistema.clientes)}, Servicios: {len(sistema.servicios)}, Reservas: {len(sistema.reservas)}")


if __name__ == "__main__":
    ejecutar_simulacion()