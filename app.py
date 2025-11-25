"""
Sendora - Multi-Platform Bulk Messaging Application
Main application file with GUI and orchestration logic
Platform-specific logic is in the 'platforms' folder
"""

# Standard library imports
import pandas as pd
import time
import random
import os
import threading
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import requests  # For API calls

# Platform-specific sender imports
from platforms.whatsapp import send_message_whatsapp
from platforms.email_sender import send_email_smtp
from platforms.sms import send_message_sms, detect_android_device
from platforms.messenger import send_message_messenger

# Utility imports
from utils.driver import create_driver, PROFILE_DIR, HEADLESS

# Check SMS availability
try:
    from ppadb.client import Client as AdbClient
    ADB_AVAILABLE = True
except ImportError:
    ADB_AVAILABLE = False

# ==================== CONFIG ====================
MIN_DELAY = 3
MAX_DELAY = 7
# ===============================================

# --- AI Text Generation Function ---
def generate_ai_text(prompt, log_fn):
    """
    Generate text using Hugging Face's free Inference API.
    Uses a working text generation model.
    """
    if not prompt or not prompt.strip():
        return "Please enter a prompt to generate text."

    try:
        # Try multiple models in case one is unavailable
        models_to_try = [
            "gpt2",  # Basic GPT-2
            "distilgpt2",  # Distilled GPT-2
            "microsoft/DialoGPT-small",  # Conversational AI
            "google/flan-t5-small",  # Instruction-following model
        ]

        # Use a placeholder API key - user needs to get their own from huggingface.co

        openai_key = ""  # Add your OpenAI API key here for better results (optional)
        # Get your key from: https://platform.openai.com/api-keys
        if openai_key:
            try:
                log_fn("🤖 Trying OpenAI API first...")
                openai_headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                openai_payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": f"Write a professional message: {prompt}"}],
                    "max_tokens": 150,
                    "temperature": 0.7
                }
                openai_response = requests.post("https://api.openai.com/v1/chat/completions",
                                              headers=openai_headers, json=openai_payload, timeout=30)

                if openai_response.status_code == 200:
                    result = openai_response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        generated_text = result["choices"][0]["message"]["content"].strip()
                        return generated_text

                log_fn(f"⚠️ OpenAI failed: {openai_response.status_code}")
            except Exception as e:
                log_fn(f"⚠️ OpenAI error: {str(e)[:50]}")

        log_fn("🤖 Generating AI text...")
        log_fn(f"🔑 Using API key: {headers['Authorization'][:20]}...")

        # Test API key with a simple request first
        test_url = "https://huggingface.co/api/whoami-v2"
        try:
            test_response = requests.get(test_url, headers=headers, timeout=10)
            if test_response.status_code == 200:
                log_fn("✅ API key is valid")
            else:
                log_fn(f"⚠️ API key test failed: {test_response.status_code}")
        except Exception as e:
            log_fn(f"⚠️ API key test error: {str(e)[:50]}")

        last_error = None

        for model in models_to_try:
            try:
                API_URL = f"https://api-inference.huggingface.co/models/{model}"

                # Prepare the payload based on model type
                if "flan" in model.lower():
                    # FLAN-T5 models need instruction format
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 150,
                            "temperature": 0.8,
                            "do_sample": True,
                        }
                    }
                elif "dialogpt" in model.lower():
                    # DialoGPT works better with conversational input
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 100,
                            "temperature": 0.7,
                            "do_sample": True,
                        }
                    }
                else:
                    # Default GPT-style models
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 100,
                            "temperature": 0.7,
                            "do_sample": True,
                        }
                    }

                log_fn(f"🤖 Trying model: {model}")

                # Make API request
                response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
                log_fn(f"📡 HTTP Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        # Remove the original prompt from the response
                        if generated_text.startswith(prompt):
                            generated_text = generated_text[len(prompt):].strip()
                        elif "Write a message:" in prompt and generated_text.startswith("Write a message:"):
                            generated_text = generated_text[len("Write a message:"):].strip()
                        return generated_text if generated_text else "No text generated."
                    else:
                        return "Unexpected API response format."
                elif response.status_code == 503:
                    log_fn(f"⚠️ Model {model} is loading, trying next...")
                    continue  # Try next model
                elif response.status_code == 403:
                    return "❌ Invalid API key. Please get a free Hugging Face API key from huggingface.co/settings/tokens"
                elif response.status_code == 410:
                    log_fn(f"⚠️ Model {model} unavailable (410 Gone), trying next...")
                    continue  # Try next model
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    log_fn(f"⚠️ Model {model} failed: {error_msg}")
                    last_error = error_msg
                    continue  # Try next model

            except Exception as e:
                last_error = str(e)
                log_fn(f"⚠️ Model {model} error: {str(e)[:100]}")
                continue

            # Small delay between model attempts
            time.sleep(1)

        # If all models failed, provide a professional business template based on the prompt
        log_fn("⚠️ All external AI models failed, generating professional business template...")

        # Create a professional business message template based on keywords in the prompt
        prompt_lower = prompt.lower()

        if "handmade" in prompt_lower and "artisan" in prompt_lower and "website" in prompt_lower:
            return """Hello [Company Name],

Namaste,

This is Razu Shrestha, CEO and Founder of NepaTronix Engineering Solution Pvt. Ltd.
We create modern, high-performing, and fully automated websites for handmade and artisan product businesses to help them showcase their craftsmanship beautifully, attract global buyers, and build a strong digital brand identity.

Our website system for handmade businesses includes:
• Dynamic product catalog with images, categories, materials, and pricing
• Online inquiry, quotation, and wholesale order system
• Story and craftsmanship section to highlight your brand's heritage
• Artisan profiles to showcase the people behind the craft
• Blog and SEO tools for international visibility
• Clean, elegant, and mobile-friendly design that reflects your artistry
• Dealer and export management panel

We follow Google's highest website standards:
SEO: 100% optimized
Performance: 100%
Accessibility: 100%
Best Practices: 100%

Additionally, we provide:
• Super-fast VPS hosting (100GB space)
• 1-year AMC free
• Unlimited technical support

Here are a few examples of our work:
https://event-solution.vercel.app/
https://himalayasummitevents.com/
https://campsitenepal.com/
https://karnorr.com/

You can learn more about us from our company profile:
https://docs.google.com/document/d/1XjA1dCGYDhQvkWzDx9vFLmPq8Pwh1i_GJ_IDfLm4C2Y/edit?usp=sharing

If you're planning to take your handmade business online or upgrade your current website, please share your available time or fill out this meeting form:
https://forms.gle/8bDXVzgh2AEPiZ3U9

Best regards,
Razu Shrestha
CEO & Founder
NepaTronix Engineering Solution Pvt. Ltd.
9803661701"""

        elif "professional" in prompt_lower and "service" in prompt_lower:
            return """Hello [Company Name],

Namaste,

This is Razu Shrestha, CEO and Founder of NepaTronix Engineering Solution Pvt. Ltd.
We specialize in providing comprehensive professional services tailored to meet your business needs. Our team of experts is committed to delivering high-quality solutions that drive results and help your business grow.

Our professional services include:
• Strategic business consulting and planning
• Digital transformation and automation solutions
• Custom software development and integration
• Data analytics and business intelligence
• Cloud infrastructure and migration services
• Cybersecurity and compliance management
• Training and capacity building programs

We follow industry best practices and standards:
• ISO 9001:2015 certified processes
• Agile development methodology
• 99.9% service uptime guarantee
• 24/7 technical support
• Regular security audits and updates

Additionally, we provide:
• Comprehensive project documentation
• Post-implementation support and maintenance
• Performance monitoring and optimization
• Scalable and flexible service packages

Here are a few examples of our work:
https://event-solution.vercel.app/
https://himalayasummitevents.com/
https://campsitenepal.com/

You can learn more about us from our company profile:
https://docs.google.com/document/d/1XjA1dCGYDhQvkWzDx9vFLmPq8Pwh1i_GJ_IDfLm4C2Y/edit?usp=sharing

If you're interested in our professional services, please share your requirements or fill out this consultation form:
https://forms.gle/8bDXVzgh2AEPiZ3U9

Best regards,
Razu Shrestha
CEO & Founder
NepaTronix Engineering Solution Pvt. Ltd.
9803661701"""

        elif "website" in prompt_lower and "development" in prompt_lower:
            return """Hello [Company Name],

Namaste,

This is Razu Shrestha, CEO and Founder of NepaTronix Engineering Solution Pvt. Ltd.
We create modern, high-performing, and fully automated websites for businesses looking to establish a strong online presence. Our expert team delivers cutting-edge web solutions that engage visitors and drive conversions.

Our website development services include:
• Custom website design and development
• E-commerce platform setup and integration
• Content management system (CMS) implementation
• Mobile-responsive design and optimization
• Search engine optimization (SEO) setup
• Website security and performance optimization
• Analytics and tracking integration

We follow Google's highest website standards:
SEO: 100% optimized
Performance: 100%
Accessibility: 100%
Best Practices: 100%

Additionally, we provide:
• Super-fast VPS hosting (100GB space)
• 1-year AMC free
• Unlimited technical support
• Domain registration and SSL certificates

Here are a few examples of our work:
https://event-solution.vercel.app/
https://himalayasummitevents.com/
https://campsitenepal.com/
https://karnorr.com/

You can learn more about us from our company profile:
https://docs.google.com/document/d/1XjA1dCGYDhQvkWzDx9vFLmPq8Pwh1i_GJ_IDfLm4C2Y/edit?usp=sharing

If you're planning to take your business online or upgrade your current website, please share your available time or fill out this meeting form:
https://forms.gle/8bDXVzgh2AEPiZ3U9

Best regards,
Razu Shrestha
CEO & Founder
NepaTronix Engineering Solution Pvt. Ltd.
9803661701"""

        else:
            # Generic professional business template
            return """Hello [Company Name],

Namaste,

This is Razu Shrestha, CEO and Founder of NepaTronix Engineering Solution Pvt. Ltd.
We specialize in delivering innovative technology solutions that help businesses thrive in the digital age. Our team combines technical expertise with business acumen to create solutions that drive real results.

Our services include:
• Custom software development
• Web application development
• Digital marketing and SEO
• Business process automation
• Data analytics and insights
• Cloud solutions and infrastructure
• Technical consulting and support

We follow industry best practices:
• Modern development frameworks and technologies
• Agile development methodology
• Quality assurance and testing
• Security-first approach
• Scalable and maintainable solutions

Additionally, we provide:
• Comprehensive project documentation
• Post-launch support and maintenance
• Performance monitoring and optimization
• Training and knowledge transfer

Here are a few examples of our work:
https://event-solution.vercel.app/
https://himalayasummitevents.com/
https://campsitenepal.com/

You can learn more about us from our company profile:
https://docs.google.com/document/d/1XjA1dCGYDhQvkWzDx9vFLmPq8Pwh1i_GJ_IDfLm4C2Y/edit?usp=sharing

If you're interested in our services, please share your requirements or fill out this consultation form:
https://forms.gle/8bDXVzgh2AEPiZ3U9

Best regards,
Razu Shrestha
CEO & Founder
NepaTronix Engineering Solution Pvt. Ltd.
9803661701"""

    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error. Check your internet connection."
    except Exception as e:
        log_fn(f"AI Generation Error: {str(e)}")
        return f"❌ Error generating text: {str(e)}"

# --- Helper: Extract numeric digits from phone numbers ---
def extract_phone_digits(phone_str):
    """
    Extract only numeric digits from a phone number string.
    Examples:
        "+977-980-3661701" -> "9779803661701"
        "Phone: 9779803661701" -> "9779803661701"
        "977 (980) 366-1701" -> "9779803661701"
    """
    digits = re.sub(r'\D', '', str(phone_str))
    return digits.strip()

# ====================GUI CODE STARTS HERE ====================
# --- Global UI Components Storage ---
attachment_entry = None
email_config_section = None
sms_config_section = None
messenger_config_section = None
platform_var = None

def update_ui_for_platform():
    """Show/hide UI elements based on selected platform"""
    global email_config_section, sms_config_section, messenger_config_section
    platform = platform_var.get()
    
    if platform == "Email":
        email_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        if sms_config_section:
            sms_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()
    elif platform == "SMS":
        if sms_config_section:
            sms_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        email_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()
    elif platform == "Messenger":
        if messenger_config_section:
            messenger_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        email_config_section.pack_forget()
        if sms_config_section:
            sms_config_section.pack_forget()
    else:
        email_config_section.pack_forget()
        if sms_config_section:
            sms_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()

# ================= MODERN REACTIVE GUI =================
root = tk.Tk()
root.title("🚀 growHigh - Bulk Sender (WhatsApp | Email | SMS | Messenger)")
root.geometry("1000x950")
root.resizable(True, True)
root.minsize(800, 750)

# ===== ULTRA MODERN COLOR SCHEME =====
BG_PRIMARY = "#0D1117"
BG_SECONDARY = "#161B22"
CARD_BG = "#0D1117"
CARD_BORDER = "#30363D"
FG_PRIMARY = "#E6EDF3"
FG_SECONDARY = "#8B949E"
ACCENT_MAIN = "#58A6FF"
ACCENT_GREEN = "#3FB950"
ACCENT_RED = "#F85149"
ACCENT_YELLOW = "#D29922"
ACCENT_BLUE = "#79C0FF"
HOVER_BG = "#21262D"
BUTTON_HOVER = "#238636"

root.configure(bg=BG_PRIMARY)

# Modern Fonts
FONT_TITLE = ("Consolas", 28, "bold")
FONT_SUBTITLE = ("Consolas", 11)
FONT_LABEL = ("Consolas", 11, "bold")
FONT_TEXT = ("Consolas", 10)
FONT_LOG = ("Courier New", 9)

# ===== MAIN LAYOUT =====
# Top banner
banner = tk.Frame(root, bg=ACCENT_MAIN, height=3)
banner.pack(fill=tk.X, pady=0)

# Header
header = tk.Frame(root, bg=BG_SECONDARY, height=90)
header.pack(fill=tk.X, padx=0, pady=0)
header.pack_propagate(False)

header_content = tk.Frame(header, bg=BG_SECONDARY)
header_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

title = tk.Label(header_content, text="🚀 growHigh", font=FONT_TITLE, bg=BG_SECONDARY, fg=ACCENT_GREEN)
title.pack(anchor=tk.W)
subtitle = tk.Label(header_content, text="Professional Bulk Sender - WhatsApp, Email, SMS & Messenger", font=FONT_SUBTITLE, bg=BG_SECONDARY, fg=FG_SECONDARY)
subtitle.pack(anchor=tk.W, pady=(3, 0))

# Separator line
sep1 = tk.Frame(root, bg=CARD_BORDER, height=1)
sep1.pack(fill=tk.X, padx=0)

# ===== CSV COMPARISON TOOL BUTTON (Navigation Bar) =====
nav_bar = tk.Frame(root, bg=BG_SECONDARY, height=50)
nav_bar.pack(fill=tk.X)
nav_bar.pack_propagate(False)

nav_content = tk.Frame(nav_bar, bg=BG_SECONDARY)
nav_content.pack(pady=10)

def open_csv_compare_tool():
    """Open CSV comparison tool window"""
    compare_window = tk.Toplevel(root)
    compare_window.title("📊 CSV Comparison Tool")
    compare_window.geometry("750x700")
    compare_window.configure(bg=BG_PRIMARY)
    compare_window.resizable(True, True)
    
    # Header
    header = tk.Frame(compare_window, bg=BG_SECONDARY, height=70)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)
    
    header_content = tk.Frame(header, bg=BG_SECONDARY)
    header_content.pack(pady=15, padx=25)
    
    tk.Label(header_content, text="🔄", font=("Arial", 20), bg=BG_SECONDARY, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 12))
    tk.Label(header_content, text="CSV Comparison Tool", font=("Consolas", 16, "bold"), bg=BG_SECONDARY, fg=FG_PRIMARY).pack(side=tk.LEFT)
    tk.Label(header_content, text="Find unique contacts", font=("Consolas", 9), bg=BG_SECONDARY, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(15, 0))
    
    # Separator
    tk.Frame(compare_window, bg=CARD_BORDER, height=1).pack(fill=tk.X)
    
    # Main content with scroll
    main_frame = tk.Frame(compare_window, bg=BG_PRIMARY)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
    
    # Instructions
    instructions = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    instructions.pack(fill=tk.X, pady=(0, 15))
    
    inst_header = tk.Frame(instructions, bg=CARD_BG)
    inst_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(inst_header, text="ℹ️", font=("Arial", 16), bg=CARD_BG, fg=ACCENT_YELLOW).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(inst_header, text="How It Works", font=("Consolas", 11, "bold"), bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    inst_list = tk.Frame(instructions, bg=CARD_BG)
    inst_list.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    tk.Label(inst_list, text="1️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=0, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Select Original CSV (contacts already messaged)", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="2️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=1, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Select New CSV (full contact list)", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="3️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=2, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Tool removes duplicates - keeps only unique contacts from File B", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="4️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=3, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Save unique contacts as new CSV - ready to use!", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    # File A Selection
    file_a_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    file_a_section.pack(fill=tk.X, pady=(0, 12))
    
    fa_header = tk.Frame(file_a_section, bg=CARD_BG)
    fa_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(fa_header, text="📁", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(fa_header, text="File A - Original CSV (Already Messaged)", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    file_a_frame = tk.Frame(file_a_section, bg=CARD_BG)
    file_a_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    file_a_entry = tk.Entry(file_a_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    file_a_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    def browse_file_a():
        path = filedialog.askopenfilename(parent=compare_window, title="Select Original CSV (File A)", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            file_a_entry.delete(0, tk.END)
            file_a_entry.insert(0, path)
    
    browse_a_btn = tk.Button(file_a_frame, text="📂 BROWSE", command=browse_file_a, bg=ACCENT_GREEN, fg="#000000",
                            font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=18, pady=8, cursor="hand2")
    browse_a_btn.pack(side=tk.LEFT)
    
    # File B Selection
    file_b_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    file_b_section.pack(fill=tk.X, pady=(0, 12))
    
    fb_header = tk.Frame(file_b_section, bg=CARD_BG)
    fb_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(fb_header, text="📁", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(fb_header, text="File B - New CSV (Full Contact List)", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    file_b_frame = tk.Frame(file_b_section, bg=CARD_BG)
    file_b_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    file_b_entry = tk.Entry(file_b_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    file_b_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    def browse_file_b():
        path = filedialog.askopenfilename(parent=compare_window, title="Select New CSV (File B)", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            file_b_entry.delete(0, tk.END)
            file_b_entry.insert(0, path)
    
    browse_b_btn = tk.Button(file_b_frame, text="📂 BROWSE", command=browse_file_b, bg=ACCENT_GREEN, fg="#000000",
                            font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=18, pady=8, cursor="hand2")
    browse_b_btn.pack(side=tk.LEFT)
    
    # Compare button section (Step 1: Compare files)
    compare_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    compare_section.pack(fill=tk.X, pady=(0, 12))
    
    compare_info = tk.Frame(compare_section, bg=CARD_BG)
    compare_info.pack(fill=tk.X, padx=20, pady=(12, 5))
    
    tk.Label(compare_info, text="🔄", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(compare_info, text="Compare & Save", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    tk.Label(compare_info, text="Find unique contacts and save to file", font=("Consolas", 8),
             bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))
    
    compare_btn_frame = tk.Frame(compare_section, bg=CARD_BG)
    compare_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    # Results display
    results_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    results_section.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
    
    res_header = tk.Frame(results_section, bg=CARD_BG)
    res_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(res_header, text="📊", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(res_header, text="Comparison Results", font=("Consolas", 10, "bold"), bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    results_text = scrolledtext.ScrolledText(results_section, height=10, font=("Consolas", 9), bg=BG_SECONDARY, fg=ACCENT_GREEN,
                                            state=tk.DISABLED, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
    results_text.pack(padx=20, pady=(0, 12), fill=tk.BOTH, expand=True)
    
    def log_result(msg):
        results_text.configure(state=tk.NORMAL)
        results_text.insert(tk.END, f"{msg}\n")
        results_text.see(tk.END)
        results_text.configure(state=tk.DISABLED)
    
    # Save button section (Step 2: Save results) - Initially hidden
    save_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    
    save_info = tk.Frame(save_section, bg=CARD_BG)
    save_info.pack(fill=tk.X, padx=20, pady=(12, 8))
    
    tk.Label(save_info, text="💾", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_YELLOW).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(save_info, text="Step 2: Save Unique Contacts", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    save_btn_frame = tk.Frame(save_section, bg=CARD_BG)
    save_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    output_entry = tk.Entry(save_btn_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    # Global variable to store comparison result
    comparison_result = {'df_unique': None, 'unique_count': 0}
    
    # Compare function (Step 1)
    def compare_files():
        file_a = file_a_entry.get().strip()
        file_b = file_b_entry.get().strip()
        
        if not file_a or not os.path.exists(file_a):
            messagebox.showerror("Error", "Please select Original CSV (File A)")
            return
        
        if not file_b or not os.path.exists(file_b):
            messagebox.showerror("Error", "Please select New CSV (File B)")
            return
        
        try:
            results_text.configure(state=tk.NORMAL)
            results_text.delete(1.0, tk.END)
            results_text.configure(state=tk.DISABLED)
            
            log_result("═" * 60)
            log_result("🔄 STARTING CSV COMPARISON...")
            log_result("═" * 60)
            log_result("")
            
            # Read both CSV files
            df_a = pd.read_csv(file_a)
            df_b = pd.read_csv(file_b)
            
            log_result(f"✅ File A loaded: {len(df_a)} rows")
            log_result(f"✅ File B loaded: {len(df_b)} rows")
            log_result("")
            
            # Detect platform based on columns
            platform_detected = None
            contact_col = None
            
            if 'phone' in df_a.columns or 'Phone' in df_a.columns:
                platform_detected = "WhatsApp/SMS"
                contact_col = 'phone' if 'phone' in df_a.columns else 'Phone'
            elif 'email' in df_a.columns or 'Email' in df_a.columns:
                platform_detected = "Email"
                contact_col = 'email' if 'email' in df_a.columns else 'Email'
            elif 'username' in df_a.columns or 'Username' in df_a.columns:
                platform_detected = "Messenger"
                contact_col = 'username' if 'username' in df_a.columns else 'Username'
            else:
                # Use first column as contact column
                contact_col = df_a.columns[0]
                platform_detected = "Unknown"
                log_result(f"⚠️ No standard column found, using: '{contact_col}'")
            
            log_result(f"📱 Platform detected: {platform_detected}")
            log_result(f"📋 Using column: '{contact_col}'")
            log_result("")
            
            # Extract and normalize contacts from File A
            if platform_detected == "WhatsApp/SMS":
                contacts_a = set(df_a[contact_col].astype(str).apply(extract_phone_digits))
            else:
                contacts_a = set(df_a[contact_col].astype(str).str.strip().str.lower())
            
            contacts_a = {c for c in contacts_a if c and c != 'nan'}
            log_result(f"🔍 Unique contacts in File A: {len(contacts_a)}")
            
            # Find unique contacts in File B (not in File A)
            unique_rows = []
            duplicate_count = 0
            
            for idx, row in df_b.iterrows():
                contact = str(row[contact_col])
                
                if platform_detected == "WhatsApp/SMS":
                    normalized = extract_phone_digits(contact)
                else:
                    normalized = contact.strip().lower()
                
                if normalized and normalized != 'nan':
                    if normalized not in contacts_a:
                        unique_rows.append(row)
                    else:
                        duplicate_count += 1
            
            log_result(f"🔄 Contacts in File B: {len(df_b)}")
            log_result(f"✅ Unique contacts (NOT in File A): {len(unique_rows)}")
            log_result(f"♻️  Duplicates (already in File A): {duplicate_count}")
            log_result("")
            
            if not unique_rows:
                log_result("⚠️  NO UNIQUE CONTACTS FOUND!")
                log_result("All contacts in File B already exist in File A.")
                log_result("")
                messagebox.showinfo("No Unique Contacts", "❌ No unique contacts found!\n\nAll contacts in File B already exist in File A.")
                return
            
            # Ask user where to save
            output_file = filedialog.asksaveasfilename(
                parent=compare_window,
                title="Save Unique Contacts",
                defaultextension=".csv",
                initialfile="unique_contacts.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not output_file:
                log_result("⚠️ Save cancelled by user")
                return
            
            # Create new DataFrame with unique contacts
            df_unique = pd.DataFrame(unique_rows)
            
            log_result(f"💾 Saving {len(unique_rows)} contacts to file...")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                log_result(f"📁 Created directory: {output_dir}")
            
            # Save to output file
            df_unique.to_csv(output_file, index=False)
            
            # Verify file was saved
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                log_result(f"✅ File saved successfully! ({file_size} bytes)")
            else:
                log_result(f"⚠️ Warning: File save reported success but file not found")
            
            log_result("")
            log_result("═" * 60)
            log_result("✅ SUCCESS!")
            log_result("═" * 60)
            log_result(f"📊 Found {len(unique_rows)} unique contacts")
            log_result(f"💾 Saved to: {output_file}")
            log_result("")
            log_result("✨ File is ready to use in the main app!")
            log_result("═" * 60)
            
            # Auto-load the new file into main CSV entry (if it exists)
            try:
                csv_entry.delete(0, tk.END)
                csv_entry.insert(0, output_file)
                log(f"✅ Loaded unique contacts CSV: {output_file}")
            except:
                pass  # csv_entry or log() not yet defined
            
            # Ask if user wants to open the folder
            response = messagebox.askyesno("✅ Success!", 
                              f"Found {len(unique_rows)} unique contacts!\n\n" +
                              f"💾 Saved to:\n{output_file}\n\n" +
                              f"📤 File has been auto-loaded in the main app.\n\n" +
                              f"Do you want to open the folder?")
            
            if response:
                # Open folder containing the file
                import subprocess
                folder_path = os.path.dirname(output_file)
                subprocess.Popen(f'explorer /select,"{output_file}"')
            
        except Exception as e:
            log_result("")
            log_result(f"❌ ERROR: {str(e)}")
            log_result(f"Full error: {repr(e)}")
            log_result("")
            messagebox.showerror("Error", f"Failed to compare CSV files:\n\n{str(e)}")
    
    compare_btn = tk.Button(compare_btn_frame, text="🔄  COMPARE & SAVE", command=compare_files, 
                           bg=ACCENT_MAIN, fg="white", font=("Consolas", 11, "bold"), 
                           relief=tk.FLAT, bd=0, padx=30, pady=14, cursor="hand2")
    compare_btn.pack(fill=tk.X)
    
    def on_compare_btn_enter(event):
        compare_btn.config(bg="#4A8DD6")
    
    def on_compare_btn_leave(event):
        compare_btn.config(bg=ACCENT_MAIN)
    
    compare_btn.bind("<Enter>", on_compare_btn_enter)
    compare_btn.bind("<Leave>", on_compare_btn_leave)

csv_compare_btn = tk.Button(nav_content, text="🔄  CSV COMPARE TOOL", command=open_csv_compare_tool,
                            bg=ACCENT_MAIN, fg="white", font=("Consolas", 10, "bold"),
                            relief=tk.FLAT, bd=0, padx=25, pady=10, cursor="hand2")
csv_compare_btn.pack()

def on_nav_compare_enter(event):
    csv_compare_btn.config(bg="#4A8DD6")

def on_nav_compare_leave(event):
    csv_compare_btn.config(bg=ACCENT_MAIN)

csv_compare_btn.bind("<Enter>", on_nav_compare_enter)
csv_compare_btn.bind("<Leave>", on_nav_compare_leave)

# Separator line
sep2 = tk.Frame(root, bg=CARD_BORDER, height=1)
sep2.pack(fill=tk.X, padx=0)

# Main scrollable container
main_container = tk.Frame(root, bg=BG_PRIMARY)
main_container.pack(fill=tk.BOTH, expand=True)

# Create canvas for scrolling
canvas = tk.Canvas(main_container, bg=BG_PRIMARY, highlightthickness=0)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add scrollbar
scrollbar = tk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview, bg=BG_SECONDARY)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure canvas
canvas.configure(yscrollcommand=scrollbar.set)

# Create frame inside canvas
content_frame = tk.Frame(canvas, bg=BG_PRIMARY)
canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

# Bind canvas resize
def on_canvas_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    # Make content frame width match canvas width
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind('<Configure>', on_canvas_configure)
content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Enable mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# Add padding to content
content_inner = tk.Frame(content_frame, bg=BG_PRIMARY)
content_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

# Replace content_frame with content_inner for all sections below
content_frame = content_inner

# ===== SECTION 0: PLATFORM SELECTOR =====
section_platform = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_platform.pack(fill=tk.X, pady=12)

def on_section_enter(event, section):
    section.config(highlightbackground=ACCENT_MAIN, highlightthickness=2)

def on_section_leave(event, section):
    section.config(highlightbackground=CARD_BORDER, highlightthickness=1)

section_platform.bind("<Enter>", lambda e: on_section_enter(e, section_platform))
section_platform.bind("<Leave>", lambda e: on_section_leave(e, section_platform))

s_platform_header = tk.Frame(section_platform, bg=CARD_BG)
s_platform_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_platform_header, text="🔀", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_platform_header, text="Select Platform", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

# Platform selection
platform_frame = tk.Frame(section_platform, bg=CARD_BG)
platform_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

platform_var = tk.StringVar(value="WhatsApp")

def on_platform_change(*args):
    selected = platform_var.get()
    log(f"📱 Platform switched to: {selected}")
    update_ui_for_platform()

platform_var.trace('w', on_platform_change)

platforms = ["WhatsApp", "Email", "SMS", "Messenger"]
for platform in platforms:
    platform_rb = tk.Radiobutton(
        platform_frame, text=f"  {platform}",
        variable=platform_var, value=platform,
        bg=CARD_BG, fg=FG_PRIMARY, selectcolor=BG_SECONDARY,
        activebackground=HOVER_BG, activeforeground=ACCENT_GREEN,
        font=FONT_TEXT, highlightthickness=0
    )
    platform_rb.pack(side=tk.LEFT, padx=10, pady=5)

# Country Code Selector (for WhatsApp/SMS)
country_code_frame = tk.Frame(platform_frame, bg=CARD_BG)
country_code_frame.pack(fill=tk.X, pady=(10, 0))

tk.Label(country_code_frame, text="🌍 Country Code:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 10))

# Country codes dictionary
COUNTRY_CODES = {
    "Nepal (+977)": "+977",
    "India (+91)": "+91",
    "USA (+1)": "+1",
    "UK (+44)": "+44",
    "Canada (+1)": "+1",
    "Australia (+61)": "+61",
    "Germany (+49)": "+49",
    "France (+33)": "+33",
    "Japan (+81)": "+81",
    "China (+86)": "+86",
    "South Korea (+82)": "+82",
    "Singapore (+65)": "+65",
    "UAE (+971)": "+971",
    "Saudi Arabia (+966)": "+966",
    "Malaysia (+60)": "+60",
    "Thailand (+66)": "+66",
    "Philippines (+63)": "+63",
    "Indonesia (+62)": "+62",
    "Pakistan (+92)": "+92",
    "Bangladesh (+880)": "+880",
    "Sri Lanka (+94)": "+94",
    "Mexico (+52)": "+52",
    "Brazil (+55)": "+55",
    "Argentina (+54)": "+54",
    "South Africa (+27)": "+27",
    "New Zealand (+64)": "+64",
    "Spain (+34)": "+34",
    "Italy (+39)": "+39",
    "Netherlands (+31)": "+31",
    "Belgium (+32)": "+32",
    "Switzerland (+41)": "+41",
    "Austria (+43)": "+43",
    "Sweden (+46)": "+46",
    "Norway (+47)": "+47",
    "Denmark (+45)": "+45",
    "Poland (+48)": "+48",
    "Russia (+7)": "+7",
    "Turkey (+90)": "+90",
    "Egypt (+20)": "+20",
    "Nigeria (+234)": "+234",
    "Kenya (+254)": "+254",
    "Vietnam (+84)": "+84",
    "Hong Kong (+852)": "+852",
}

country_code_var = tk.StringVar(value="Nepal (+977)")
country_code_dropdown = ttk.Combobox(
    country_code_frame,
    textvariable=country_code_var,
    values=list(COUNTRY_CODES.keys()),
    state="readonly",
    font=FONT_TEXT,
    width=20
)
country_code_dropdown.pack(side=tk.LEFT)
country_code_dropdown.current(0)  # Default to Nepal

# Label to show selected code
selected_code_label = tk.Label(country_code_frame, text="+977", font=("Consolas", 10, "bold"), bg=CARD_BG, fg=ACCENT_GREEN)
selected_code_label.pack(side=tk.LEFT, padx=(10, 0))

def on_country_change(event=None):
    selected_country = country_code_var.get()
    code = COUNTRY_CODES.get(selected_country, "+977")
    selected_code_label.config(text=code)
    log(f"🌍 Country code changed to: {code}")

country_code_dropdown.bind("<<ComboboxSelected>>", on_country_change)

# ===== SECTION 0.5: EMAIL CREDENTIALS (Hidden by default) =====
email_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

email_config_section.bind("<Enter>", lambda e: on_section_enter(e, email_config_section))
email_config_section.bind("<Leave>", lambda e: on_section_leave(e, email_config_section))

s_email_header = tk.Frame(email_config_section, bg=CARD_BG)
s_email_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_email_header, text="🔐", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_email_header, text="Email Sender Credentials", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_email_header, text="Enter your Gmail/Outlook credentials", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

email_input_frame = tk.Frame(email_config_section, bg=CARD_BG)
email_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

tk.Label(email_input_frame, text="Sender Email:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_sender_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
email_sender_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))

tk.Label(email_input_frame, text="App Password (Gmail: 16-char App Password):", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_password_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, show="•")
email_password_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))

tk.Label(email_input_frame, text="Email Subject:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_subject_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
email_subject_entry.pack(fill=tk.X, ipady=6, pady=(0, 15))

# ===== SECTION 0.6: SMS CONFIGURATION (Hidden by default) =====
sms_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

sms_config_section.bind("<Enter>", lambda e: on_section_enter(e, sms_config_section))
sms_config_section.bind("<Leave>", lambda e: on_section_leave(e, sms_config_section))

s_sms_header = tk.Frame(sms_config_section, bg=CARD_BG)
s_sms_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_sms_header, text="📱", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_sms_header, text="Android Phone via USB", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_sms_header, text="Connect your Android phone with USB Debugging enabled", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

sms_input_frame = tk.Frame(sms_config_section, bg=CARD_BG)
sms_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

# Device connection test button
def test_phone_connection():
    """Test Android phone connection via ADB"""
    log("📱 Testing Android phone connection...")
    device = detect_android_device(log)
    if device:
        log("✅ Phone connection test PASSED!")
        log("💡 You can now send SMS messages.")
    else:
        log("❌ Phone connection test FAILED!")
        log("💡 See SMS_SETUP_GUIDE.md for troubleshooting.")

test_phone_btn = tk.Button(sms_input_frame, text="🔌 TEST PHONE CONNECTION", command=test_phone_connection, 
                           bg=ACCENT_MAIN, fg="#FFFFFF", font=("Consolas", 9, "bold"), 
                           relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
test_phone_btn.pack(fill=tk.X, pady=(0, 10))

def on_test_phone_enter(event):
    test_phone_btn.config(bg="#4A8DD6")

def on_test_phone_leave(event):
    test_phone_btn.config(bg=ACCENT_MAIN)

test_phone_btn.bind("<Enter>", on_test_phone_enter)
test_phone_btn.bind("<Leave>", on_test_phone_leave)

# SMS Setup instructions
sms_info_label = tk.Label(sms_input_frame, 
                          text="🤖 Auto-click ENABLED: App will try to click send button automatically!\n" + 
                               "💡 Enable USB Debugging: Settings → Developer Options → USB Debugging\n" +
                               "📚 Full setup guide: SMS_SETUP_GUIDE.md",
                          font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_GREEN, justify=tk.LEFT)
sms_info_label.pack(anchor=tk.W, pady=(5, 10))

# ===== SECTION 0.7: MESSENGER CONFIGURATION (Hidden by default) =====
messenger_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

messenger_config_section.bind("<Enter>", lambda e: on_section_enter(e, messenger_config_section))
messenger_config_section.bind("<Leave>", lambda e: on_section_leave(e, messenger_config_section))

s_messenger_header = tk.Frame(messenger_config_section, bg=CARD_BG)
s_messenger_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_messenger_header, text="💬", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_messenger_header, text="Facebook Messenger", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_messenger_header, text="Login to Facebook Messenger in the browser window", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

messenger_input_frame = tk.Frame(messenger_config_section, bg=CARD_BG)
messenger_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

# Messenger login test button
def test_messenger_login():
    """Test Messenger login by opening browser"""
    log("📱 Opening Messenger for login test...")
    try:
        driver = create_driver()
        driver.get("https://www.messenger.com")
        log("✅ Browser opened. Please log in to Facebook Messenger.")
        log("💡 Keep browser open for sending messages.")
    except Exception as e:
        log(f"❌ Failed to open browser: {e}")

test_messenger_btn = tk.Button(messenger_input_frame, text="🔐 TEST MESSENGER LOGIN", command=test_messenger_login, 
                           bg=ACCENT_MAIN, fg="#FFFFFF", font=("Consolas", 9, "bold"), 
                           relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
test_messenger_btn.pack(fill=tk.X, pady=(0, 10))

def on_test_messenger_enter(event):
    test_messenger_btn.config(bg="#4A8DD6")

def on_test_messenger_leave(event):
    test_messenger_btn.config(bg=ACCENT_MAIN)

test_messenger_btn.bind("<Enter>", on_test_messenger_enter)
test_messenger_btn.bind("<Leave>", on_test_messenger_leave)

# Messenger Setup instructions
messenger_info_label = tk.Label(messenger_input_frame, 
                          text="📋 CSV must have 'username' column (Facebook username or profile ID)\n" + 
                               "💡 Login to Facebook Messenger when browser opens\n" +
                               "⚡ Messages will be sent automatically after login",
                          font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_GREEN, justify=tk.LEFT)
messenger_info_label.pack(anchor=tk.W, pady=(5, 10))

# ===== SECTION 1: CSV FILE INPUT =====
section1 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section1.pack(fill=tk.X, pady=12)

section1.bind("<Enter>", lambda e: on_section_enter(e, section1))
section1.bind("<Leave>", lambda e: on_section_leave(e, section1))

s1_header = tk.Frame(section1, bg=CARD_BG)
s1_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s1_header, text="📂", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s1_header, text="Import Contacts (CSV)", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s1_header, text="Select a CSV file with phone numbers", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

s1_input = tk.Frame(section1, bg=CARD_BG)
s1_input.pack(fill=tk.X, padx=20, pady=(0, 15))

csv_entry = tk.Entry(s1_input, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)

def on_csv_focus_in(event):
    csv_entry.config(bg=BG_SECONDARY)

def on_csv_focus_out(event):
    csv_entry.config(bg=HOVER_BG)

csv_entry.bind("<FocusIn>", on_csv_focus_in)
csv_entry.bind("<FocusOut>", on_csv_focus_out)

def browse_csv():
    path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if path:
        csv_entry.delete(0, tk.END)
        csv_entry.insert(0, path)
        log(f"✅ CSV loaded: {path}")

browse_btn = tk.Button(s1_input, text="📁 BROWSE", command=browse_csv, bg=ACCENT_GREEN, fg="#000000", 
                       font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
browse_btn.pack(side=tk.LEFT)

def on_browse_enter(event):
    browse_btn.config(bg=BUTTON_HOVER, fg="#FFF")

def on_browse_leave(event):
    browse_btn.config(bg=ACCENT_GREEN, fg="#000000")

browse_btn.bind("<Enter>", on_browse_enter)
browse_btn.bind("<Leave>", on_browse_leave)

# ===== SECTION 1.5: FILE ATTACHMENT (OPTIONAL) =====
section_attachment = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_attachment.pack(fill=tk.X, pady=12)

section_attachment.bind("<Enter>", lambda e: on_section_enter(e, section_attachment))
section_attachment.bind("<Leave>", lambda e: on_section_leave(e, section_attachment))

sa_header = tk.Frame(section_attachment, bg=CARD_BG)
sa_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(sa_header, text="📎", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(sa_header, text="Attach File (Optional)", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(sa_header, text="Select a file to send with each message (PDF, PNG, JPG, etc.)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

sa_input = tk.Frame(section_attachment, bg=CARD_BG)
sa_input.pack(fill=tk.X, padx=20, pady=(0, 15))

attachment_entry = tk.Entry(sa_input, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
attachment_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)

def on_attachment_focus_in(event):
    attachment_entry.config(bg=BG_SECONDARY)

def on_attachment_focus_out(event):
    attachment_entry.config(bg=HOVER_BG)

attachment_entry.bind("<FocusIn>", on_attachment_focus_in)
attachment_entry.bind("<FocusOut>", on_attachment_focus_out)

def browse_attachment():
    path = filedialog.askopenfilename(
        filetypes=[
            ("All Files", "*.*"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.png;*.jpg;*.jpeg;*.gif"),
            ("Documents", "*.doc;*.docx;*.xls;*.xlsx")
        ]
    )
    if path:
        attachment_entry.delete(0, tk.END)
        attachment_entry.insert(0, path)
        log(f"✅ Attachment selected: {os.path.basename(path)}")

browse_attachment_btn = tk.Button(sa_input, text="📎 BROWSE FILE", command=browse_attachment, bg=ACCENT_YELLOW, fg="#000000", 
                       font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
browse_attachment_btn.pack(side=tk.LEFT, padx=(0, 10))

def on_browse_attachment_enter(event):
    browse_attachment_btn.config(bg="#E8B923", fg="#000000")

def on_browse_attachment_leave(event):
    browse_attachment_btn.config(bg=ACCENT_YELLOW, fg="#000000")

browse_attachment_btn.bind("<Enter>", on_browse_attachment_enter)
browse_attachment_btn.bind("<Leave>", on_browse_attachment_leave)

# Clear attachment button
clear_attachment_btn = tk.Button(sa_input, text="✖ CLEAR", command=lambda: (attachment_entry.delete(0, tk.END), log("🗑️ Attachment cleared")), 
                       bg=ACCENT_RED, fg="white", font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=15, pady=8, cursor="hand2")
clear_attachment_btn.pack(side=tk.LEFT)

def on_clear_attachment_enter(event):
    clear_attachment_btn.config(bg="#E03C3C")

def on_clear_attachment_leave(event):
    clear_attachment_btn.config(bg=ACCENT_RED)

clear_attachment_btn.bind("<Enter>", on_clear_attachment_enter)
clear_attachment_btn.bind("<Leave>", on_clear_attachment_leave)

# ===== SECTION 1.7: ADVANCED SETTINGS (WhatsApp) =====
section_advanced = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_advanced.pack(fill=tk.X, pady=12)

section_advanced.bind("<Enter>", lambda e: on_section_enter(e, section_advanced))
section_advanced.bind("<Leave>", lambda e: on_section_leave(e, section_advanced))

adv_header = tk.Frame(section_advanced, bg=CARD_BG)
adv_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(adv_header, text="⚙️", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(adv_header, text="Advanced Settings", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(adv_header, text="Configure delay time, row range, and filters", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

adv_content = tk.Frame(section_advanced, bg=CARD_BG)
adv_content.pack(fill=tk.X, padx=20, pady=(10, 15))

# Skip 01 numbers checkbox
skip_01_var = tk.BooleanVar(value=False)
skip_01_check = tk.Checkbutton(
    adv_content, text="  Skip phone numbers starting with 01",
    variable=skip_01_var,
    bg=CARD_BG, fg=FG_PRIMARY, selectcolor=BG_SECONDARY,
    activebackground=HOVER_BG, activeforeground=ACCENT_GREEN,
    font=FONT_TEXT, highlightthickness=0
)
skip_01_check.pack(anchor=tk.W, pady=(0, 15))

# Delay time configuration
delay_frame = tk.Frame(adv_content, bg=CARD_BG)
delay_frame.pack(fill=tk.X, pady=(0, 15))

tk.Label(delay_frame, text="Message Delay (seconds):", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 10))
delay_entry = tk.Entry(delay_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=10)
delay_entry.insert(0, "60")  # Default 60 seconds
delay_entry.pack(side=tk.LEFT, ipady=5)
tk.Label(delay_frame, text="(Time between messages)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))

# Row range configuration
range_frame = tk.Frame(adv_content, bg=CARD_BG)
range_frame.pack(fill=tk.X, pady=(0, 5))

tk.Label(range_frame, text="Send to rows:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(range_frame, text="From:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 5))
row_start_entry = tk.Entry(range_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=8)
row_start_entry.insert(0, "1")  # Default start from row 1
row_start_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 10))

tk.Label(range_frame, text="To:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 5))
row_end_entry = tk.Entry(range_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=8)
row_end_entry.insert(0, "999999")  # Default to very large number (all rows)
row_end_entry.pack(side=tk.LEFT, ipady=5)
tk.Label(range_frame, text="(Leave 'To' as large number for all rows)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))

# ===== SECTION 1.5: AI TEXT GENERATION =====
ai_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
ai_section.pack(fill=tk.X, pady=12)

ai_section.bind("<Enter>", lambda e: on_section_enter(e, ai_section))
ai_section.bind("<Leave>", lambda e: on_section_leave(e, ai_section))

ai_header = tk.Frame(ai_section, bg=CARD_BG)
ai_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(ai_header, text="🤖", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(ai_header, text="AI Text Generator", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(ai_header, text="Generate messages using AI (requires free HuggingFace API key)", font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_YELLOW).pack(anchor=tk.W, pady=(5, 0))

# API Key info
api_info = tk.Frame(ai_section, bg=CARD_BG)
api_info.pack(fill=tk.X, padx=20, pady=(0, 10))
tk.Label(api_info, text="🔑", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_YELLOW).pack(side=tk.LEFT, padx=(0, 5))
tk.Label(api_info, text="Get free API key at: huggingface.co/settings/tokens (replace x's in code)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT)

ai_input_frame = tk.Frame(ai_section, bg=CARD_BG)
ai_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

tk.Label(ai_input_frame, text="Prompt:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
ai_prompt_entry = tk.Entry(ai_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
ai_prompt_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))
ai_prompt_entry.insert(0, "Write a professional business outreach message for handmade/artisan businesses about our website development services. Include company introduction, services list, portfolio examples, and call to action.")

ai_buttons_frame = tk.Frame(ai_input_frame, bg=CARD_BG)
ai_buttons_frame.pack(fill=tk.X, pady=(0, 10))

generate_btn = tk.Button(ai_buttons_frame, text="🎯 Generate", bg=ACCENT_BLUE, fg="white",
                        font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=15, pady=6, cursor="hand2")
generate_btn.pack(side=tk.LEFT, padx=(0, 10))

copy_btn = tk.Button(ai_buttons_frame, text="📋 Copy to Message", bg=ACCENT_YELLOW, fg="#000000",
                    font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=15, pady=6, cursor="hand2")
copy_btn.pack(side=tk.LEFT)

clear_btn = tk.Button(ai_buttons_frame, text="🗑️ Clear", bg=HOVER_BG, fg=FG_PRIMARY,
                     font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=15, pady=6, cursor="hand2")
clear_btn.pack(side=tk.LEFT)

ai_output_frame = tk.Frame(ai_section, bg=CARD_BG)
ai_output_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

tk.Label(ai_output_frame, text="Generated Text:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
ai_output_text = tk.Text(ai_output_frame, height=4, width=80, wrap=tk.WORD, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT,
                        relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=8, pady=6)
ai_output_text.pack(fill=tk.X, expand=True)

# AI Functions
def generate_ai_text_gui():
    """Generate AI text and display in GUI"""
    prompt = ai_prompt_entry.get().strip()
    if not prompt:
        messagebox.showwarning("Empty Prompt", "Please enter a prompt to generate text.")
        return

    # Disable button during generation
    generate_btn.config(state=tk.DISABLED, text="⏳ Generating...")
    ai_output_text.delete("1.0", tk.END)
    ai_output_text.insert("1.0", "Generating AI text... Please wait...")

    def ai_worker():
        result = generate_ai_text(prompt, log)
        root.after(0, lambda: update_ai_output(result))

    def update_ai_output(result):
        ai_output_text.delete("1.0", tk.END)
        ai_output_text.insert("1.0", result)
        generate_btn.config(state=tk.NORMAL, text="🎯 Generate")

    threading.Thread(target=ai_worker, daemon=True).start()

def copy_to_message():
    """Copy generated AI text to message composer"""
    ai_text = ai_output_text.get("1.0", tk.END).strip()
    if ai_text and ai_text != "Generating AI text... Please wait...":
        current_msg = msg_text.get("1.0", tk.END).strip()
        if current_msg:
            # Append to existing message
            msg_text.insert(tk.END, "\n\n" + ai_text)
        else:
            # Replace empty message
            msg_text.insert("1.0", ai_text)
        log("📋 AI text copied to message composer")
    else:
        messagebox.showwarning("No Text", "Please generate AI text first.")

def clear_ai_output():
    """Clear AI output"""
    ai_output_text.delete("1.0", tk.END)
    ai_prompt_entry.delete(0, tk.END)
    ai_prompt_entry.insert(0, "Write a professional business outreach message for handmade/artisan businesses about our website development services. Include company introduction, services list, portfolio examples, and call to action.")

# Bind AI buttons
generate_btn.config(command=generate_ai_text_gui)
copy_btn.config(command=copy_to_message)
clear_btn.config(command=clear_ai_output)

# ===== SECTION 2: MESSAGE COMPOSER =====
section2 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section2.pack(fill=tk.BOTH, expand=True, pady=12)

section2.bind("<Enter>", lambda e: on_section_enter(e, section2))
section2.bind("<Leave>", lambda e: on_section_leave(e, section2))

s2_header = tk.Frame(section2, bg=CARD_BG)
s2_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s2_header, text="💬", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s2_header, text="Compose Your Message", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s2_header, text="Type your message here (use \\n for line breaks)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

msg_text = tk.Text(section2, height=10, width=80, wrap=tk.WORD, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, 
                   relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
msg_text.pack(padx=20, pady=(10, 10), fill=tk.BOTH, expand=True)

def update_char_count(event=None):
    char_count = len(msg_text.get("1.0", tk.END)) - 1
    char_label.config(text=f"Characters: {char_count}")

msg_text.bind("<KeyRelease>", update_char_count)

char_label = tk.Label(section2, text="Characters: 0", font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_YELLOW)
char_label.pack(anchor=tk.E, padx=20, pady=(0, 15))

# ===== SECTION 3: ACTION BUTTONS =====
button_section = tk.Frame(content_frame, bg=BG_PRIMARY)
button_section.pack(fill=tk.X, pady=15)

start_btn = tk.Button(button_section, text="▶  START SENDING", bg=ACCENT_GREEN, fg="#000000",
                     font=("Consolas", 11, "bold"), relief=tk.FLAT, bd=0, padx=30, pady=12, cursor="hand2")
start_btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

stop_btn = tk.Button(button_section, text="⏹  STOP", bg=ACCENT_RED, fg="white",
                    font=("Consolas", 11, "bold"), relief=tk.FLAT, bd=0, padx=30, pady=12, cursor="hand2")
stop_btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

download_btn = tk.Button(button_section, text="📥 DOWNLOAD FAILED", bg=ACCENT_BLUE, fg="white",
                        font=("Consolas", 11, "bold"), relief=tk.FLAT, bd=0, padx=30, pady=12, cursor="hand2", state=tk.DISABLED)
download_btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

def on_start_enter(event):
    start_btn.config(bg=BUTTON_HOVER)

def on_start_leave(event):
    start_btn.config(bg=ACCENT_GREEN, fg="#000000")

def on_stop_enter(event):
    stop_btn.config(bg="#E03C3C")

def on_stop_leave(event):
    stop_btn.config(bg=ACCENT_RED)

def on_download_enter(event):
    download_btn.config(bg="#2563EB")

def on_download_leave(event):
    download_btn.config(bg=ACCENT_BLUE)

start_btn.bind("<Enter>", on_start_enter)
start_btn.bind("<Leave>", on_start_leave)
stop_btn.bind("<Enter>", on_stop_enter)
stop_btn.bind("<Leave>", on_stop_leave)
download_btn.bind("<Enter>", on_download_enter)
download_btn.bind("<Leave>", on_download_leave)

# ===== SECTION 4: ACTIVITY LOG =====
section3 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section3.pack(fill=tk.BOTH, expand=True, pady=12)

section3.bind("<Enter>", lambda e: on_section_enter(e, section3))
section3.bind("<Leave>", lambda e: on_section_leave(e, section3))

s3_header = tk.Frame(section3, bg=CARD_BG)
s3_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s3_header, text="📋", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s3_header, text="Activity Log", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

log_box = scrolledtext.ScrolledText(section3, height=12, font=FONT_LOG, bg=BG_SECONDARY, fg=ACCENT_GREEN, 
                                    state=tk.DISABLED, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
log_box.pack(padx=20, pady=(5, 15), fill=tk.BOTH, expand=True)

# ===== SECTION 5: STATISTICS =====
section4 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section4.pack(fill=tk.X, pady=12)

section4.bind("<Enter>", lambda e: on_section_enter(e, section4))
section4.bind("<Leave>", lambda e: on_section_leave(e, section4))

s4_header = tk.Frame(section4, bg=CARD_BG)
s4_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s4_header, text="📊", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s4_header, text="Statistics", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

stats_frame = tk.Frame(section4, bg=CARD_BG)
stats_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

# Stat boxes
def create_stat_box(parent, label, color):
    box = tk.Frame(parent, bg=HOVER_BG, relief=tk.FLAT, bd=0)
    box.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
    tk.Label(box, text=label, font=("Consolas", 9), bg=HOVER_BG, fg=FG_SECONDARY).pack(pady=(8, 2))
    value_label = tk.Label(box, text="0", font=("Consolas", 20, "bold"), bg=HOVER_BG, fg=color)
    value_label.pack(pady=(2, 8))
    return value_label

stats_sent = create_stat_box(stats_frame, "✅ Sent", ACCENT_GREEN)
stats_failed = create_stat_box(stats_frame, "❌ Failed", ACCENT_RED)
stats_pending = create_stat_box(stats_frame, "⏳ Pending", ACCENT_YELLOW)

# logging helper (thread-safe)
def log(msg):
    def _append():
        log_box.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        log_box.insert(tk.END, f"[{timestamp}] {msg}\n")
        log_box.see(tk.END)
        log_box.configure(state=tk.DISABLED)
    root.after(0, _append)

# stop event for threads
stop_event = threading.Event()

# Global variable to store failed CSV path
failed_csv_path = None

def download_failed_csv():
    global failed_csv_path
    if failed_csv_path and os.path.exists(failed_csv_path):
        try:
            os.startfile(failed_csv_path)  # Windows
            log(f"📂 Opened failed contacts CSV: {failed_csv_path}")
        except Exception as e:
            log(f"❌ Could not open failed CSV: {e}")
    else:
        messagebox.showinfo("No Failed Contacts", "No failed contacts CSV available. Run a campaign first.")

# Worker thread
def start_sending():
    if start_btn['state'] == tk.DISABLED:
        return
    csv_path = csv_entry.get().strip()
    if not csv_path or not os.path.exists(csv_path):
        messagebox.showerror("CSV not found", f"CSV file not found: {csv_path}")
        return
    
    message = msg_text.get("1.0", tk.END).strip()
    attachment_path = attachment_entry.get().strip() if attachment_entry.get().strip() else None
    
    # Check if there's either a message or an attachment
    if not message and not attachment_path:
        messagebox.showerror("No content", "Please type a message or attach a file to send.")
        return

    stop_event.clear()
    start_btn.config(state=tk.DISABLED)

    def worker():
        driver = None
        sent_count = 0
        failed_count = 0
        
        # Get platform and attachment
        platform = platform_var.get()
        attachment_path = attachment_entry.get().strip() if attachment_entry.get().strip() else None
        
        # Get advanced settings
        skip_01_numbers = skip_01_var.get()
        
        # Get delay time
        try:
            delay_seconds = int(delay_entry.get().strip())
            if delay_seconds < 1:
                delay_seconds = 60
        except ValueError:
            delay_seconds = 60
            log("⚠️ Invalid delay value, using default 60 seconds")
        
        # Get row range
        try:
            row_start = int(row_start_entry.get().strip())
            if row_start < 1:
                row_start = 1
        except ValueError:
            row_start = 1
            log("⚠️ Invalid start row, using row 1")
        
        try:
            row_end = int(row_end_entry.get().strip())
        except ValueError:
            row_end = 999999
            log("⚠️ Invalid end row, processing all rows")
        
        # Validate email credentials if using Email platform
        if platform == "Email":
            sender_email = email_sender_entry.get().strip()
            sender_password = email_password_entry.get().strip()
            email_subject = email_subject_entry.get().strip()
            
            if not sender_email or not sender_password:
                messagebox.showerror("Missing Credentials", "Please enter email and password.")
                start_btn.config(state=tk.NORMAL)
                return
            
            if not email_subject:
                email_subject = "Message from growHigh"
        
        # Detect Android device if using SMS platform
        android_device = None
        if platform == "SMS":
            log("📱 Detecting Android device...")
            android_device = detect_android_device(log)
            if not android_device:
                messagebox.showerror("No Phone Detected", "Cannot detect Android phone. Please connect phone and enable USB Debugging.")
                start_btn.config(state=tk.NORMAL)
                return
            log("✅ Android device ready for SMS sending")
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            log(f"❌ CSV Error: {e}")
            start_btn.config(state=tk.NORMAL)
            return

        # Extract contacts based on platform
        rows = []
        row_mapping = {}  # Map processed contact to original row data
        
        if platform == "Email":
            # Email mode: look for email column
            email_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('email', 'email_address', 'mail', 'recipient'):
                    email_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if email_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    email_raw = str(r[email_col]).strip()
                    
                    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_raw):
                        log(f"⚠️ Skipping invalid email: {email_raw}")
                        continue
                    
                    name = "Friend"
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    # Personalize message with name
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {name},\n\n{personalized_msg}"
                    rows.append((email_raw, personalized_msg, name))
                    row_mapping[email_raw] = r.to_dict()
            else:
                # Fallback: use first column as email
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    email_raw = str(r[first_col]).strip()
                    
                    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_raw):
                        log(f"⚠️ Skipping invalid email: {email_raw}")
                        continue
                    
                    name = "Friend"
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {name},\n\n{personalized_msg}"
                    rows.append((email_raw, personalized_msg, name))
                    row_mapping[email_raw] = r.to_dict()
        
        elif platform == "Messenger":
            # Messenger mode: look for username column
            username_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('username', 'user', 'facebook_username', 'fb_username', 'messenger_username'):
                    username_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if username_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    username_raw = str(r[username_col]).strip()
                    
                    if not username_raw or username_raw == 'nan':
                        log(f"⚠️ Skipping empty username at row {row_number}")
                        continue
                    
                    # Use username as name if no name column, otherwise use name column
                    name = username_raw
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    # Personalize message: replace {{name}} with name, add "Hello {username}" prefix
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {username_raw},\n\n{personalized_msg}"
                    rows.append((username_raw, personalized_msg, username_raw))
                    row_mapping[username_raw] = r.to_dict()
            else:
                # Fallback: use first column as username
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    username_raw = str(r[first_col]).strip()
                    
                    if not username_raw or username_raw == 'nan':
                        log(f"⚠️ Skipping empty username at row {row_number}")
                        continue
                    
                    # Use username as name if no name column, otherwise use second column as name
                    name = username_raw
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    # Personalize message: replace {{name}} with name, add "Hello {username}" prefix
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {username_raw},\n\n{personalized_msg}"
                    rows.append((username_raw, personalized_msg, username_raw))
                    row_mapping[username_raw] = r.to_dict()
        
        else:
            # WhatsApp/SMS mode: look for phone column
            phone_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('phone','phone_number','phone_number_e164','number'):
                    phone_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if phone_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    phone_raw = str(r[phone_col]).strip()
                    phone_clean = extract_phone_digits(phone_raw)
                    
                    # Skip numbers starting with 01
                    if skip_01_numbers and phone_clean.startswith("01"):
                        log(f"⏭️ Skipping number starting with 01: {phone_raw}")
                        continue
                    
                    name = "Friend"
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    if phone_clean:
                        # If attachment exists but no message, don't add greeting
                        if attachment_path and (not message or not message.strip()):
                            personalized_msg = ""  # Empty message, only attachment
                        else:
                            # Normal message with greeting
                            personalized_msg = f"Hello {name},\n\n{message}"
                        rows.append((phone_clean, personalized_msg, name))
                        row_mapping[phone_clean] = r.to_dict()
                    else:
                        log(f"⚠️ Skipping invalid phone: {phone_raw}")
            else:
                # fallback: use first column as phone
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    phone_raw = str(r[first_col]).strip()
                    phone_clean = extract_phone_digits(phone_raw)
                    
                    # Skip numbers starting with 01
                    if skip_01_numbers and phone_clean.startswith("01"):
                        log(f"⏭️ Skipping number starting with 01: {phone_raw}")
                        continue
                    
                    name = "Sir/Ma'am"
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    if phone_clean:
                        # If attachment exists but no message, don't add greeting
                        if attachment_path and (not message or not message.strip()):
                            personalized_msg = ""  # Empty message, only attachment
                        else:
                            # Normal message with greeting
                            personalized_msg = f"Hello {name},\n\n{message}"
                        rows.append((phone_clean, personalized_msg, name))
                        row_mapping[phone_clean] = r.to_dict()
                    else:
                        log(f"⚠️ Skipping invalid phone: {phone_raw}")

        if not rows:
            if platform == "Email":
                contact_type = "emails"
            elif platform == "Messenger":
                contact_type = "usernames"
            else:
                contact_type = "phone numbers"
            log(f"❌ No valid {contact_type} found.")
            start_btn.config(state=tk.NORMAL)
            return

        log(f"🚀 Starting broadcast to {len(rows)} contacts via {platform}...")
        log(f"📂 CSV File: {csv_path}")
        log(f"📊 Row Range: {row_start} to {row_end}")
        if platform == "WhatsApp":
            log(f"⏱️ Delay between messages: {delay_seconds} seconds")
            if skip_01_numbers:
                log(f"⏭️ Skipping numbers starting with 01: ENABLED")
        if attachment_path:
            log(f"📎 Attachment: {os.path.basename(attachment_path)}")

        # Create driver for WhatsApp or Messenger
        if platform in ["WhatsApp", "Messenger"]:
            try:
                log(f"🌐 Initializing Chrome browser...")
                driver = create_driver()
                log(f"✅ Browser started successfully")
            except Exception as e:
                log(f"❌ Browser startup failed: {e}")
                import traceback
                log(f"📋 Error details: {traceback.format_exc()[:300]}")
                start_btn.config(state=tk.NORMAL)
                return

            if platform == "WhatsApp":
                # Open WhatsApp Web
                log("🌐 Opening WhatsApp Web...")
                try:
                    driver.get("https://web.whatsapp.com")
                    log(f"✅ WhatsApp Web loaded: {driver.current_url[:50]}")
                except Exception as e:
                    log(f"❌ Failed to open WhatsApp Web: {e}")
                    driver.quit()
                    start_btn.config(state=tk.NORMAL)
                    return
                
                time.sleep(2)
                if "web.whatsapp.com" in driver.current_url and "qr" in driver.page_source.lower():
                    log("📱 Please scan QR code in WhatsApp Web. Waiting 20s...")
                    time.sleep(20)
                else:
                    log("✅ Already logged in to WhatsApp Web")
            elif platform == "Messenger":
                # Open Messenger
                driver.get("https://www.messenger.com")
                time.sleep(2)
                if "login" in driver.current_url.lower():
                    log("📱 Please log in to Facebook Messenger. Waiting 20s...")
                    time.sleep(20)

        sent_count = 0
        failed_list = []
        failed_rows = []  # Store original row data for failed contacts
        
        # Sending loop based on platform
        if platform == "Email":
            # Email sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_email, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_email} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_email_smtp(target_email, email_subject, msg, sender_email, sender_password, log, stop_event, attachment_path)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_email)
                        failed_rows.append(row_mapping[target_email])
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_email}: {e}")
                    failed_list.append(target_email)
                    failed_rows.append(row_mapping[target_email])
                    stats_failed.config(text=str(len(failed_list)))
                
                if stop_event.is_set():
                    break
        
        elif platform == "SMS":
            # SMS sending loop
            # Get selected country code
            selected_country = country_code_var.get()
            country_code = COUNTRY_CODES.get(selected_country, "+977")
            log(f"🌍 Using country code: {country_code}")
            
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_phone, msg, name = row_data
                
                # Add country code if not already present
                target_phone = str(target_phone).strip()
                if not target_phone.startswith("+") and not target_phone.startswith("00"):
                    # Remove leading zeros if present
                    target_phone = target_phone.lstrip("0")
                    # Add country code
                    full_phone = country_code + target_phone
                else:
                    full_phone = target_phone
                
                log(f"[{i}/{len(rows)}] → {full_phone} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_sms(android_device, full_phone, msg, log, stop_event, delay_seconds)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_phone)
                        failed_rows.append(row_mapping[target_phone])
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_phone}: {e}")
                    failed_list.append(target_phone)
                    failed_rows.append(row_mapping[target_phone])
                    stats_failed.config(text=str(len(failed_list)))
                
                if stop_event.is_set():
                    break
        
        elif platform == "Messenger":
            # Messenger sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_username, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_username} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_messenger(driver, target_username, msg, log, stop_event, attachment_path)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_username)
                        failed_rows.append(row_mapping[target_username])
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_username}: {e}")
                    failed_list.append(target_username)
                    failed_rows.append(row_mapping[target_username])
                    stats_failed.config(text=str(len(failed_list)))
                
                # Short delay between messages
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                for remaining in range(int(delay), 0, -1):
                    if stop_event.is_set():
                        break
                    if remaining <= 3:
                        log(f"  ⏳ {remaining}s...")
                    time.sleep(1)
                
                if stop_event.is_set():
                    break
        
        else:
            # WhatsApp sending loop
            # Get selected country code
            selected_country = country_code_var.get()
            country_code = COUNTRY_CODES.get(selected_country, "+977")
            log(f"🌍 Using country code: {country_code}")
            
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_phone, msg, name = row_data
                
                # Add country code if not already present
                target_phone = str(target_phone).strip()
                if not target_phone.startswith("+") and not target_phone.startswith("00"):
                    # Remove leading zeros if present
                    target_phone = target_phone.lstrip("0")
                    # Add country code
                    full_phone = country_code + target_phone
                else:
                    full_phone = target_phone
                
                log(f"[{i}/{len(rows)}] → {full_phone} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_whatsapp(driver, full_phone, msg, log, stop_event, attachment_path, delay_seconds)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_phone)
                        failed_rows.append(row_mapping[target_phone])
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_phone}: {e}")
                    failed_list.append(target_phone)
                    failed_rows.append(row_mapping[target_phone])
                    stats_failed.config(text=str(len(failed_list)))
                
                # Delay is now handled inside send_message_whatsapp function with countdown
                
                if stop_event.is_set():
                    break

        log(f"✅ COMPLETE: {sent_count}/{len(rows)} sent | ❌ Failed: {len(failed_list)}")
        if failed_list:
            log("📌 Failed contacts: " + ", ".join(failed_list[:5]))
            
            # Create failed contacts CSV
            if failed_rows:
                global failed_csv_path
                failed_df = pd.DataFrame(failed_rows)
                failed_csv_path = csv_path.replace('.csv', '_failed.csv')
                failed_df.to_csv(failed_csv_path, index=False)
                log(f"💾 Failed contacts saved to: {failed_csv_path}")
                log(f"📊 Failed CSV contains {len(failed_rows)} rows with {len(failed_df.columns)} columns")
                download_btn.config(state=tk.NORMAL)
        
        if platform in ["WhatsApp", "Messenger"]:
            try:
                driver.quit()
            except Exception:
                pass
        
        start_btn.config(state=tk.NORMAL)
        stats_pending.config(text="0")

    threading.Thread(target=worker, daemon=True).start()

def stop_sending():
    stop_event.set()
    log("⏹ Stop requested. Completing current message...")

start_btn.config(command=start_sending)
stop_btn.config(command=stop_sending)
download_btn.config(command=download_failed_csv)

log("🎉 App ready – select CSV, type message, and click START SENDING")
root.mainloop() 