# main.py

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from classify import classify_urgency
from db import insert_patient, get_all_patients

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
@app.get("/intake", response_class=HTMLResponse)
async def intake_form(request: Request):
    return templates.TemplateResponse("intake.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    symptoms: str = Form(...),
):
    urgency = await classify_urgency(symptoms)
    insert_patient(name, symptoms, urgency)
    return templates.TemplateResponse("intake.html", {
        "request": request,
        "submitted": True,
        "urgency": urgency
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    patients = get_all_patients()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "patients": patients
    })
