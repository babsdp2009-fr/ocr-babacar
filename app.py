import os
import re
import cv2
import io
import numpy as np
import streamlit as st
from PIL import Image
import pytesseract
import pypdf
from docx import Document  
from fpdf import FPDF  

# =====================================================================
# 1. CONFIGURATION TESSERACT (Solution adaptative Local PC vs Serveur)
# =====================================================================
chemin_tesseract_windows = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if os.path.exists(chemin_tesseract_windows):
    pytesseract.pytesseract.tesseract_cmd = chemin_tesseract_windows
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
else:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# Configuration générale de la page
st.set_page_config(page_title="ID Scanner Recto-Verso", layout="wide", initial_sidebar_state="collapsed")

# --- INITIALISATION DE LA MÉMOIRE ---
if "donnees_combinees" not in st.session_state:
    st.session_state.donnees_combinees = None
if "texte_brut_total" not in st.session_state:
    st.session_state.texte_brut_total = ""

# --- DESIGN & CSS STYLE SCRIPT ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #0f0c20 0%, #15102a 100%);
        color: #ffffff;
    }
    
    .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        font-size: 3.2rem;
        background: linear-gradient(45deg, #ff007f, #7f00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 5px;
    }
    
    .subtitle {
        text-align: center;
        color: #b3b0cb;
        font-size: 1.2rem;
        margin-bottom: 40px;
    }

    div[data-testid="stVerticalBlock"] > div:has(div.stImage) {
        background-color: #1e1938;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #7f00ff, #ff007f) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        font-size: 1.1rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 0, 127, 0.6) !important;
    }
    
    .id-card-box {
        background-color: #1a153a;
        border-left: 5px solid #00ffcc;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">OCR de Babacar</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Scanner Intelligent de Cartes d\'Identité (Recto / Verso)</p>', unsafe_allow_html=True)

# --- FONCTION DE TRAITEMENT D'IMAGE & OCR ---
def executer_ocr(image_pil):
    try:
        img_cv = np.array(image_pil)
        if len(img_cv.shape) == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        img_gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Amélioration du contraste pour les textes plastifiés / sécurisés
        img_traitee = cv2.adaptiveThreshold(img_gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        texte = pytesseract.image_to_string(Image.fromarray(img_traitee), lang='fra+eng', config='--psm 3')
        return texte
    except Exception:
        return ""

# --- FONCTION D'EXTRACTION DES INFORMATIONS ---
def extraire_donnees_id(texte_total):
    champs = {
        "Numéro de Carte / ID": "Non détecté",
        "Nom": "Non détecté",
        "Prénom(s)": "Non détecté",
        "Date de Naissance": "Non détecté",
        "Sexe": "Non détecté",
        "Lieu de Naissance / Adresse": "Non détecté"
    }
    
    lignes = [l.strip() for l in texte_total.split('\n') if l.strip()]
    
    for i, ligne in enumerate(lignes):
        ligne_majuscule = ligne.upper()
        
        # 1. Extraction du Nom
        if "NOM" in ligne_majuscule and ":" in ligne:
            champs["Nom"] = ligne.split(":", 1)[1].strip()
        elif "SURNAME" in ligne_majuscule and i+1 < len(lignes):
            champs["Nom"] = lignes[i+1].strip()
            
        # 2. Extraction du Prénom
        if "PRENOM" in ligne_majuscule and ":" in ligne:
            champs["Prénom(s)"] = ligne.split(":", 1)[1].strip()
        elif "GIVEN NAMES" in ligne_majuscule and i+1 < len(lignes):
            champs["Prénom(s)"] = lignes[i+1].strip()

        # 3. Extraction des Dates (Format JJ/MM/AAAA ou JJ.MM.AAAA)
        dates = re.findall(r'\b\d{2}[/\.-]\d{2}[/\.-]\d{4}\b', ligne)
        if dates and champs["Date de Naissance"] == "Non détecté":
            champs["Date de Naissance"] = dates[0]
            
        # 4. Numéro de document / Numéro National (Série longue de chiffres/lettres)
        num_doc = re.search(r'\b\d{4}[0-9A-Z-\s]{6,15}\b', ligne_majuscule)
        if num_doc and champs["Numéro de Carte / ID"] == "Non détecté":
            champs["Numéro de Carte / ID"] = num_doc.group(0).strip()
            
        # 5. Détection du Sexe
        if re.search(r'\b(SEXE|SEX)\b', ligne_majuscule):
            if "M" in ligne_majuscule or "MAS" in ligne_majuscule:
                champs["Sexe"] = "M (Masculin)"
            elif "F" in ligne_majuscule or "FEM" in ligne_majuscule:
                champs["Sexe"] = "F (Féminin)"
                
        # 6. Détection d'adresse ou lieu
        if "ADRESSE" in ligne_majuscule and ":" in ligne:
            champs["Lieu de Naissance / Adresse"] = ligne.split(":", 1)[1].strip()

    # Lecture de la bande MRZ de sécurité (souvent au verso ou bas du passeport)
    mrz = re.findall(r'[A-Z0-9<]{25,30}', texte_total)
    if mrz and champs["Numéro de Carte / ID"] == "Non détecté":
        champs["Numéro de Carte / ID"] = mrz[0].replace('<', '').strip()

    return champs


# --- ZONE DE DÉPÔT DES FICHIERS ---
col_recto, col_verso = st.columns(2, gap="medium")

with col_recto:
    st.markdown("<h5 style='text-align: center; color:#7f00ff;'>📸 RECTO (Face Avant)</h5>", unsafe_allow_html=True)
    fichier_recto = st.file_uploader("Déposez le Recto", type=["png", "jpg", "jpeg", "webp"], key="recto")
    if fichier_recto:
        img_r = Image.open(fichier_recto)
        st.image(img_r, use_container_width=True)

with col_verso:
    st.markdown("<h5 style='text-align: center; color:#ff007f;'>📸 VERSO (Face Arrière)</h5>", unsafe_allow_html=True)
    fichier_verso = st.file_uploader("Déposez le Verso", type=["png", "jpg", "jpeg", "webp"], key="verso")
    if fichier_verso:
        img_v = Image.open(fichier_verso)
        st.image(img_v, use_container_width=True)


# --- BOUTON DE LANCEMENT UNIQUE ---
st.write("")
if st.button("🚀 SCANNER ET FUSIONNER LES DEUX FACES"):
    if not fichier_recto and not fichier_verso:
        st.error("⚠️ Veuillez déposer au moins une face (Recto ou Verso) de la carte.")
    else:
        with st.spinner("Analyse approfondie des deux faces en cours..."):
            texte_complet = ""
            
            if fichier_recto:
                texte_complet += "\n--- TEXTE RECTO ---\n" + executer_ocr(Image.open(fichier_recto))
            if fichier_verso:
                texte_complet += "\n--- TEXTE VERSO ---\n" + executer_ocr(Image.open(fichier_verso))
                
            st.session_state.texte_brut_total = texte_complet
            st.session_state.donnees_combinees = extraire_donnees_id(texte_complet)


# --- AFFICHAGE DES RÉSULTATS FUSIONNÉS ---
if st.session_state.donnees_combinees is not None:
    st.success("🎉 Scan et fusion terminés avec succès !")
    
    # Présentation des données extraites des deux faces
    st.markdown("<div class='id-card-box'>🪪 <b>Informations Synthétisées de la Pièce d'Identité :</b>", unsafe_allow_html=True)
    st.table(list(st.session_state.donnees_combinees.items()))
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Zone de modification manuelle
    st.session_state.texte_brut_total = st.text_area(
        "📝 Texte brut extrait combiné (Modifiable si besoin de correction) :", 
        value=st.session_state.texte_brut_total, 
        height=150
    )

    # --- ZONE D'EXPORTATION ---
    st.markdown("<h5 style='color:#00ffcc; margin-top:25px;'>📥 Télécharger le dossier d'extraction :</h5>", unsafe_allow_html=True)
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        st.download_button("📄 Fichier .txt", data=st.session_state.texte_brut_total, file_name="extraction_id.txt", mime="text/plain", use_container_width=True)
        
    with exp_col2:
        doc = Document()
        doc.add_heading("Rapport d'Extraction Pièce d'Identité", level=1)
        for k, v in st.session_state.donnees_combinees.items():
            doc.add_paragraph(f"{k} : {v}")
        doc.add_heading("Historique Texte Brut", level=2)
        doc.add_paragraph(st.session_state.texte_brut_total)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        st.download_button("📝 Fichier .docx (Word)", data=buf, file_name="extraction_id.docx", use_container_width=True)
        
    with exp_col3:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Synthese Extraction Carte d'Identite", ln=1, align="C")
        pdf.ln(10)
        for k, v in st.session_state.donnees_combinees.items():
            line = f"{k} : {v}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(200, 10, txt=line, ln=1)
        buf_p = io.BytesIO()
        pdf.output(buf_p)
        buf_p.seek(0)
        st.download_button("📕 Fichier .pdf", data=buf_p, file_name="extraction_id.pdf", use_container_width=True)