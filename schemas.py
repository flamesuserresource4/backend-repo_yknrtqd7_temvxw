"""
Database Schemas for PKL Management System

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name (e.g., User -> "user").

Roles:
- admin
- koordinator
- dosen
- pembimbing_industri
- mahasiswa
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import date, datetime

# ---------------------------------------------
# MASTER DATA
# ---------------------------------------------
class User(BaseModel):
    name: str = Field(..., description="Nama lengkap")
    email: EmailStr = Field(..., description="Email")
    password_hash: Optional[str] = Field(None, description="Hash password (untuk login manual)")
    role: Literal["admin", "koordinator", "dosen", "pembimbing_industri", "mahasiswa"] = Field(..., description="Peran pengguna")
    phone: Optional[str] = Field(None, description="Nomor HP")
    avatar_url: Optional[str] = Field(None, description="URL foto profil")
    is_active: bool = Field(True)

class Company(BaseModel):
    name: str
    address: str
    city: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    positions: List[str] = Field(default_factory=list, description="Daftar posisi/role yang ditawarkan")
    quota: int = Field(0, ge=0, description="Total kuota keseluruhan")

class Period(BaseModel):
    name: str = Field(..., description="Nama periode, misal: PKL 2025/Genap")
    start_date: date
    end_date: date
    description: Optional[str] = None

# ---------------------------------------------
# WORKFLOW DATA
# ---------------------------------------------
class Placement(BaseModel):
    student_id: str = Field(..., description="ID user mahasiswa")
    company_id: str = Field(..., description="ID perusahaan")
    position: Optional[str] = Field(None, description="Posisi yang dilamar/ditetapkan")
    period_id: str
    status: Literal["applied", "review", "approved", "rejected", "ongoing", "completed"] = "applied"
    notes: Optional[str] = None
    supervisor_dosen_id: Optional[str] = None
    supervisor_industri_id: Optional[str] = None

class Log(BaseModel):
    placement_id: str
    date: date
    activities: str = Field(..., description="Ringkasan aktivitas/tugas")
    hours: float = Field(..., ge=0, le=24, description="Jumlah jam kerja hari itu")
    evidence_photo_url: Optional[str] = Field(None, description="URL bukti foto")
    uploaded_at: Optional[datetime] = None
    status: Literal["submitted", "approved", "rejected"] = "submitted"
    reviewer_id: Optional[str] = None
    reviewer_note: Optional[str] = None

class Attendance(BaseModel):
    placement_id: str
    date: date
    status: Literal["hadir", "izin", "sakit", "alpa"] = "hadir"
    evidence_photo_url: Optional[str] = Field(None, description="URL bukti foto")
    uploaded_at: Optional[datetime] = None

class Evaluation(BaseModel):
    placement_id: str
    evaluator_id: str
    # Rubrik standar: teknis 40, disiplin 20, soft 20, laporan 20
    teknis: float = Field(..., ge=0, le=100)
    disiplin: float = Field(..., ge=0, le=100)
    soft_skills: float = Field(..., ge=0, le=100)
    laporan: float = Field(..., ge=0, le=100)
    total: Optional[float] = None
    notes: Optional[str] = None

class Notification(BaseModel):
    user_id: str
    title: str
    message: str
    type: Literal["info", "success", "warning", "error"] = "info"
    is_read: bool = False

# The Flames database viewer will read these via GET /schema
