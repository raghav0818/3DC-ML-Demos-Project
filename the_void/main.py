import os
# Silence TensorFlow/MediaPipe logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import time
import random
import json
import threading
from detector_engine import BioStressDetector

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1400, 900
BG_COLOR = "#050505"
ACCENT_COLOR = "#00FFDD"  # Cyan (Calm/System)
STRESS_COLOR = "#FF0044"  # Red (Lie)
TRUTH_COLOR = "#00FF66"   # Green (Truth)

# Fonts
FONT_TITLE = ("Impact", 64)
FONT_SUBTITLE = ("Consolas", 24)
FONT_Q = ("Impact", 42)
FONT_HUD = ("Consolas", 16, "bold")

# File Paths
LEADERBOARD_FILE = "leaderboard.json"

# Gen Z Question Bank
QUESTIONS = [
    "Have you ever used ChatGPT to write an entire essay?",
    "Do you currently have a crush on anyone in this room?",
    "Have you ever ghosted a friend for no reason?",
    "Is your screen time average higher than 6 hours?",
    "Do you think you are smarter than the person standing next to you?",
    "Have you ever stalked someone's location on Snap Map?",
    "Have you ever lied about your age to get into a club?",
    "Do you actually like the music you post on your story?",
    "Have you ever hooked up with a friend's ex?",
    "Do you verify your BeReal or retry it until you look good?",
    "Have you ever stolen someone else's charger?",
    "Do you judge people based on their Spotify Wrapped?",
    "Have you ever muted a close friend's story?",
    "Do you know a secret that could ruin someone's relationship?"
]

class TheVoidApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Theme & Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.title("SUTD Truth Booth: Social Edition")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(fg_color=BG_COLOR)
        
        # 2. Camera (HD)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # 3. Engine & State
        self.detector = BioStressDetector()
        self.running = True
        self.game_state = "ATTRACT" # ATTRACT, CALIBRATE, GAMEPLAY, REPORT
        
        # Game Data
        self.start_time = 0.0
        self.total_time = 0.0
        self.current_q_idx = 0
        self.questions_asked = [] # List of (Question, IsLie)
        self.lies_count = 0
        self.glitch_active = False
        self.glitch_end = 0.0
        
        self.frame_count = 0
        self.last_stress = 0.0
        
        self.frame_count = 0
        self.last_stress = 0.0
        self.last_reasons = []
        
        # Leaderboard Init
        self.leaderboard = self.load_leaderboard()
        
        # --- UI LAYOUT ---
        # Grid: 1x1 full screen container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.main_container = ctk.CTkFrame(self, fg_color="black")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Canvas for Video (Bottom Layer)
        self.canvas = ctk.CTkCanvas(self.main_container, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vid_id = None
        
        # UI Overlay (Top Layer)
        self.overlay = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.overlay.grid(row=0, column=0, sticky="nsew")
        
        # Initialize sub-screens
        self._init_screens()
        
        # Start Loop
        self.update_loop()

    def _init_screens(self):
        # 1. ATTRACT SCREEN
        self.frm_attract = ctk.CTkFrame(self.overlay, fg_color="#000000") # Solid Black
        ctk.CTkLabel(self.frm_attract, text="BIOMETRIC SCANNER", font=FONT_TITLE, text_color=ACCENT_COLOR).pack(pady=(120, 10))
        ctk.CTkLabel(self.frm_attract, text="TRUTH OR DARE // SOCIAL EDITION", font=FONT_SUBTITLE, text_color="white").pack(pady=10)
        
        # Leaderboard Widget
        self.frm_lb = ctk.CTkFrame(self.frm_attract, fg_color="#111", border_width=1, border_color="#333")
        self.frm_lb.pack(pady=30, padx=50, fill="x")
        ctk.CTkLabel(self.frm_lb, text="TOP AGENTS (FASTEST TIMES)", font=FONT_HUD, text_color="gray").pack(pady=10)
        self.lbl_lb_data = ctk.CTkLabel(self.frm_lb, text=self.get_leaderboard_text(), font=FONT_HUD, text_color="white")
        self.lbl_lb_data.pack(pady=(0, 10))
        
        ctk.CTkButton(self.frm_attract, text="INITIATE SCAN", font=("Impact", 24), 
                      fg_color=ACCENT_COLOR, text_color="black", height=60, width=300,
                      command=self.start_calibration).pack(pady=50)

        # 2. CALIBRATION (Text Overlay)
        self.lbl_calib = ctk.CTkLabel(self.overlay, text="STAY STILL\nCALIBRATING BASELINE...", 
                                      font=FONT_TITLE, text_color="yellow", bg_color="#000000")
        
        # 3. GAMEPLAY
        self.frm_game = ctk.CTkFrame(self.overlay, fg_color="transparent")
        # Header
        self.lbl_game_status = ctk.CTkLabel(self.frm_game, text="INTERROGATION IN PROCESS", font=FONT_HUD, text_color=ACCENT_COLOR)
        self.lbl_game_status.pack(pady=20)
        
        # Question Card
        self.card_q = ctk.CTkFrame(self.frm_game, fg_color="#111111", corner_radius=20, border_width=2, border_color="white")
        self.card_q.pack(pady=50, padx=50, fill="x")
        
        ctk.CTkLabel(self.card_q, text="INTERROGATOR: ASK THIS", font=FONT_HUD, text_color="gray").pack(pady=(20,5))
        self.lbl_q_text = ctk.CTkLabel(self.card_q, text="[QUESTION TEXT]", font=FONT_Q, text_color="white", wraplength=1000)
        self.lbl_q_text.pack(pady=(0, 20), padx=20)
        
        # Action Button
        self.btn_next = ctk.CTkButton(self.frm_game, text="SUBJECT ANSWERED", font=("Impact", 24),
                                      fg_color="white", text_color="black", height=80, width=400,
                                      command=self.next_question)
        self.btn_next.pack(side="bottom", pady=80)
        
        # Feedback Overlay (Hidden by default)
        self.lbl_feedback = ctk.CTkLabel(self.frm_game, text="LIE DETECTED", font=("Impact", 80), text_color=STRESS_COLOR)

        # 4. REPORT CARD
        self.frm_report = ctk.CTkFrame(self.overlay, fg_color="#000000")
        ctk.CTkLabel(self.frm_report, text="SUBJECT PROCESSED", font=FONT_TITLE, text_color="white").pack(pady=(80, 20))
        self.lbl_report_grade = ctk.CTkLabel(self.frm_report, text="GRADE: F", font=("Impact", 100), text_color=STRESS_COLOR)
        self.lbl_report_grade.pack(pady=10)
        
        self.lbl_report_stats = ctk.CTkLabel(self.frm_report, text="TIME: 45s | LIES: 3", font=FONT_TITLE, text_color="white")
        self.lbl_report_stats.pack(pady=20)
        
        # Liar's Log (Scrollable?) -> Just simple list for now
        self.frm_log = ctk.CTkScrollableFrame(self.frm_report, width=800, height=300, fg_color="#111")
        self.frm_log.pack(pady=20)
        
        ctk.CTkButton(self.frm_report, text="RESET SYSTEM", font=("Impact", 24),
                      fg_color="white", text_color="black", height=60, width=300,
                      command=self.reset_game).pack(pady=40)

        # START
        self.show_screen("ATTRACT")

    def show_screen(self, screen):
        self.frm_attract.place_forget()
        self.lbl_calib.place_forget()
        self.frm_game.place_forget()
        self.frm_report.place_forget()
        self.lbl_feedback.place_forget()
        
        if screen == "ATTRACT":
            self.frm_attract.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        elif screen == "CALIBRATE":
            self.lbl_calib.place(relx=0.5, rely=0.5, anchor="center")
        elif screen == "GAMEPLAY":
            self.frm_game.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        elif screen == "REPORT":
            self.frm_report.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

    def update_loop(self):
        if not self.running: return
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            frame = cv2.flip(frame, 1)
            
            # --- VISION ---
            # Optimize: Detect every 3rd frame
            if self.frame_count % 3 == 0:
                small = cv2.resize(frame, (640, 360))
                
                if self.game_state == "CALIBRATE":
                    self.detector.calibrate_frame(small)
                
                elif self.game_state == "GAMEPLAY":
                    # Continuous Analysis for Glitch Feedback
                    score, _, reasons = self.detector.get_stress_score(small)
                    self.last_stress = score
                    self.last_reasons = reasons
            
            # --- RENDER FX ---
            # Glitch Effect on Lie
            if self.glitch_active:
                if time.time() > self.glitch_end:
                    self.glitch_active = False
                    self.lbl_feedback.place_forget()
                else:
                    # Random RGB Shift
                    frame = self.apply_glitch(frame)
                    # Show FEEDBACK text
                    self.lbl_feedback.place(relx=0.5, rely=0.4, anchor="center")

            # --- CANVAS DRAW ---
            self.draw_to_canvas(frame)
            
        self.after(15, self.update_loop)

    def draw_to_canvas(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 2: cw=WIDTH
        if ch < 2: ch=HEIGHT
        
        img_w, img_h = img_pil.size
        ratio = max(cw/img_w, ch/img_h) # Minimize black bars (Cover)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        if new_w != img_w:
            img_pil = img_pil.resize((new_w, new_h), Image.Resampling.NEAREST)
            
        self.tk_img = ImageTk.PhotoImage(img_pil)
        
        cx, cy = cw//2, ch//2
        if self.vid_id is None:
            self.vid_id = self.canvas.create_image(cx, cy, image=self.tk_img, anchor="center")
        else:
            self.canvas.coords(self.vid_id, cx, cy)
            self.canvas.itemconfig(self.vid_id, image=self.tk_img)

    def apply_glitch(self, frame):
        # Basic channel shift or noise
        h, w, _ = frame.shape
        noise = np.random.randint(0, 50, (h, w, 3), dtype=np.uint8)
        
        if self.last_stress > 0.6: # Red Shift
            frame[:,:,2] = np.clip(frame[:,:,2] + 50, 0, 255) # Boost Red
        else: # Green Shift
            frame[:,:,1] = np.clip(frame[:,:,1] + 50, 0, 255) # Boost Green
            
        return cv2.add(frame, noise)

    # --- GAME FLOW ---

    def start_calibration(self):
        self.game_state = "CALIBRATE"
        self.show_screen("CALIBRATE")
        self.after(3000, self.end_calibration)

    def end_calibration(self):
        if self.detector.finalize_calibration():
            self.start_game()
        else:
            # Retry or Force Start (Standard Arcade behavior: Force Start if fail)
            print("Calib Fail - Using Defaults")
            self.detector.is_calibrated = True # Force
            self.detector.baseline_ear = 0.25
            self.start_game()

    def start_game(self):
        self.game_state = "GAMEPLAY"
        self.start_time = time.time()
        self.questions_asked = []
        self.lies_count = 0
        
        # Shuffle Questions
        self.session_questions = random.sample(QUESTIONS, 5)
        self.current_q_idx = 0
        
        self.refresh_question_ui()
        self.show_screen("GAMEPLAY")

    def refresh_question_ui(self):
        q_text = self.session_questions[self.current_q_idx]
        self.lbl_q_text.configure(text=f'"{q_text}"')
        self.lbl_game_status.configure(text=f"QUESTION {self.current_q_idx+1} OF 5")
        
        # Reset Glitch
        self.glitch_active = False
        self.lbl_feedback.place_forget()

    def next_question(self):
        # 1. Analyze "Last Stress" to determine Truth/Lie for this Q
        is_lie = self.last_stress > 0.6 # Threshold
        
        if is_lie:
            self.lies_count += 1
            self.trigger_glitch("LIE", self.last_reasons)
        else:
            self.trigger_glitch("TRUTH")
            
        # Log it
        self.questions_asked.append({
            "q": self.session_questions[self.current_q_idx],
            "is_lie": is_lie
        })
        
        # Delay to show glitch, then move on
        self.btn_next.configure(state="disabled")
        self.after(1500, self.advance_logic)
            
        # Log it
        self.questions_asked.append({
            "q": self.session_questions[self.current_q_idx],
            "is_lie": is_lie
        })
        
        # Delay to show glitch, then move on
        self.btn_next.configure(state="disabled")
        self.after(1500, self.advance_logic)

    def trigger_glitch(self, type_, reasons=None):
        self.glitch_active = True
        self.glitch_end = time.time() + 1.0
        
        if type_ == "LIE":
            # Show specific reason if available
            text = "DECEPTION DETECTED"
            if reasons and len(reasons) > 0:
                text = f"CRITICAL: {reasons[0]}"
            self.lbl_feedback.configure(text=text, text_color=STRESS_COLOR)
        else:
            self.lbl_feedback.configure(text="TRUTH VERIFIED", text_color=TRUTH_COLOR)

    def advance_logic(self):
        self.current_q_idx += 1
        self.btn_next.configure(state="normal")
        
        if self.current_q_idx >= 5:
            self.end_game()
        else:
            self.refresh_question_ui()

    def end_game(self):
        self.game_state = "REPORT"
        self.total_time = time.time() - self.start_time
        # Penalty: +5s per lie
        final_time_score = self.total_time + (self.lies_count * 5.0)
        
        # Grading
        grade = "B"
        if self.lies_count == 0: grade = "S (SAINT)"
        elif self.lies_count >= 3: grade = "F (LIAR)"
        
        # Update UI
        color = STRESS_COLOR if self.lies_count > 0 else TRUTH_COLOR
        self.lbl_report_grade.configure(text=f"GRADE: {grade}", text_color=color)
        self.lbl_report_stats.configure(text=f"FINAL TIME: {final_time_score:.2f}s (+{self.lies_count*5}s Pen) | LIES: {self.lies_count}")
        
        # Populate Log
        # Clear old
        for widget in self.frm_log.winfo_children(): widget.destroy()
        
        for idx, item in enumerate(self.questions_asked):
            status = "[LIE]" if item["is_lie"] else "[TRUTH]"
            color = STRESS_COLOR if item["is_lie"] else "gray"
            row_text = f"Q{idx+1}: {status} - {item['q']}"
            ctk.CTkLabel(self.frm_log, text=row_text, text_color=color, font=("Consolas", 14), anchor="w").pack(fill="x", pady=2)

        # Save Leaderboard
        self.update_leaderboard(final_time_score, self.lies_count)
        
        self.show_screen("REPORT")

    # --- LEADERBOARD ---

    def load_leaderboard(self):
        if not os.path.exists(LEADERBOARD_FILE):
            return []
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def update_leaderboard(self, time_score, lies):
        # We only rank based on Lowest Time Score
        entry = {
            "timestamp": time.ctime(),
            "score": round(time_score, 2),
            "lies": lies
        }
        self.leaderboard.append(entry)
        # Sort by score asc
        self.leaderboard.sort(key=lambda x: x["score"])
        self.leaderboard = self.leaderboard[:5] # Keep Top 5
        
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(self.leaderboard, f)
            
    def get_leaderboard_text(self):
        txt = ""
        for idx, entry in enumerate(self.leaderboard):
            txt += f"#{idx+1}: {entry['score']}s ({entry['lies']} Lies)\n"
        return txt if txt else "NO DATA YET"

    def reset_game(self):
        self.game_state = "ATTRACT"
        # Refresh Leaderboard display
        self.lbl_lb_data.configure(text=self.get_leaderboard_text())
        self.show_screen("ATTRACT")

    def on_closing(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = TheVoidApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
