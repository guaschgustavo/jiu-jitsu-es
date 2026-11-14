import json
import os
import re
import time
import unicodedata
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ARCHIVO_JSON = "academias.json"
ARCHIVO_GEOJSON = "academias.geojson"
ARCHIVO_HTML = "index.html"

NOMINATIM_HEADERS = {
    "User-Agent": "JiuJitsuEsDirectory/1.0 (contacto@jiu-jitsu.es)",
    "Accept-Language": "es",
}

PALABRAS_VALIDAS = [
    "jiu", "bjj", "gracie", "grappling", "mma", "dojo", "checkmat",
    "gfteam", "tenth planet", "10th planet", "artes marciales",
    "martial arts", "tatami", "kimura", "budo", "zenit bjj",
    "nova uniao", "carlson", "mathias ribeiro", "ases jiu"
]

PALABRAS_EXCLUIDAS = [
    "fleca", "panader", "restaurante", "bar ", "farmacia",
    "française", "francaise", "healthcare", "moto", "property",
    "luxinvest", "los atos", "castillo de la nava", "estación", "metro"
]

ACADEMIAS_SEMILLA = [
    {"nombre": "Mathias Ribeiro Team Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Mathias Ribeiro Team", "head_coach": "Prof. Mathias Ribeiro", "direccion": "Calle de Gutenberg 7, 28014 Madrid", "lat": 40.4055, "lng": -3.6766, "web": "https://mathiasribeiro.com"},
    {"nombre": "Checkmat Madrid / Samurai Jiu Jitsu", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Checkmat", "head_coach": "Equipo Checkmat", "direccion": "Calle de Juan Español 38, 28026 Madrid", "lat": 40.3879, "lng": -3.7011, "web": "https://checkmatmadrid.com"},
    {"nombre": "Lotus Club Madrid BJJ", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Lotus Club", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4250, "lng": -3.6850, "web": ""},
    {"nombre": "Tenth Planet Madrid BJJ", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "10th Planet Jiu Jitsu", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4100, "lng": -3.7150, "web": ""},
    {"nombre": "De La Riva BJJ Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "De La Riva", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.3980, "lng": -3.6920, "web": ""},
    {"nombre": "Carlson Gracie Madrid", "ciudad": "Madrid", "provincia": "Madrid", "afiliacion": "Carlson Gracie Team", "head_coach": "Instructor Certificado", "direccion": "Madrid, España", "lat": 40.4410, "lng": -3.6790, "web": ""},
    {"nombre": "Atos BJJ Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Atos Jiu-Jitsu", "head_coach": "Prof. Gustavo Galvao", "direccion": "Carrer de Pujades 77, 08005 Barcelona", "lat": 41.3965, "lng": 2.1965, "web": "https://atosbarcelona.com"},
    {"nombre": "Aranha Jiu Jitsu Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Association Aranha", "head_coach": "Prof. Yan Cabral", "direccion": "Barcelona, España", "lat": 41.3820, "lng": 2.1540, "web": ""},
    {"nombre": "Anaconda BJJ Barcelona", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Anaconda BJJ", "head_coach": "Instructor Certificado", "direccion": "Barcelona, España", "lat": 41.4020, "lng": 2.1750, "web": ""},
    {"nombre": "Templum BCN Jiu Jitsu", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "Templum BCN", "head_coach": "Instructor Certificado", "direccion": "Carrer d'Entença 113, 08015 Barcelona", "lat": 41.3812, "lng": 2.1485, "web": ""},
    {"nombre": "GFTeam Barcelona BJJ", "ciudad": "Barcelona", "provincia": "Barcelona", "afiliacion": "GFTeam", "head_coach": "Instructor Certificado", "direccion": "Barcelona, España", "lat": 41.4090, "lng": 2.1850, "web": ""},
    {"nombre": "Ases Jiu Jitsu Valencia", "ciudad": "Valencia", "provincia": "Valencia", "afiliacion": "Ases BJJ", "head_coach": "Prof. Ezequiel Zayas", "direccion": "Valencia, España", "lat": 39.4750, "lng": -0.3750, "web": "https://asesbjj.com"},
    {"nombre": "Checkmat Valencia BJJ", "ciudad": "Valencia", "provincia": "Valencia", "afiliacion": "Checkmat", "head_coach": "Instructor Certificado", "direccion": "Valencia, España", "lat": 39.4650, "lng": -0.3820, "web": ""},
    {"nombre": "Climent Club BJJ Alicante", "ciudad": "Alicante", "provincia": "Alicante", "afiliacion": "Climent Club", "head_coach": "Hermanos Climent", "direccion": "Calle Maestro Alonso 94, 03010 Alicante", "lat": 38.3585, "lng": -0.4882, "web": ""},
    {"nombre": "Checkmat Alicante BJJ", "ciudad": "Alicante", "provincia": "Alicante", "afiliacion": "Checkmat", "head_coach": "Instructor Certificado", "direccion": "Alicante, España", "lat": 38.3490, "lng": -0.4910, "web": ""},
    {"nombre": "Sutemi Academy BJJ Sevilla", "ciudad": "Sevilla", "provincia": "Sevilla", "afiliacion": "Sutemi Academy", "head_coach": "Instructor Certificado", "direccion": "Sevilla, España", "lat": 37.3950, "lng": -5.9710, "web": ""},
    {"nombre": "Roger Gracie Academy Málaga", "ciudad": "Málaga", "provincia": "Málaga", "afiliacion": "Roger Gracie Academy", "head_coach": "Instructor Certificado", "direccion": "Málaga, España", "lat": 36.7180, "lng": -4.4320, "web": ""},
    {"nombre": "Roger Gracie Academy Marbella", "ciudad": "Marbella", "provincia": "Málaga", "afiliacion": "Roger Gracie Academy", "head_coach": "Instructor Certificado", "direccion": "Marbella, Málaga", "lat": 36.5100, "lng": -4.8850, "web": ""},
    {"nombre": "Zenit BJJ Zaragoza", "ciudad": "Zaragoza", "provincia": "Zaragoza", "afiliacion": "Zenit BJJ", "head_coach": "Instructor Certificado", "direccion": "Zaragoza, España", "lat": 41.6490, "
