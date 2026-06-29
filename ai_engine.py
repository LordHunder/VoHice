import time
import threading
import io
import wave
import numpy as np
import sounddevice as sd
from pynput.keyboard import Controller

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, SAMPLE_RATE, CHANNELS

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY != "INSERISCI_QUI_LA_TUA_CHIAVE_API" else None

class AIEngine:
    def __init__(self):
        self.keyboard = Controller()
        self.is_listening = False
        self.translate_to_english = False
        self.status_callback = None
        self.volume_callback = None
        self.clipboard_callback = None
        
        self.audio_data = []
        self.silence_chunks = 0
        self.speech_chunks = 0
        self.state = "IDLE"

    def toggle_listening(self, translate_mode, status_cb, volume_cb, clipboard_cb=None):
        self.translate_to_english = translate_mode
        self.status_callback = status_cb
        self.volume_callback = volume_cb
        self.clipboard_callback = clipboard_cb
        
        if self.is_listening:
            self.is_listening = False
            if self.status_callback:
                self.status_callback("green", "Pronto")
            if self.volume_callback:
                self.volume_callback(0.0)
            return False
        else:
            self.is_listening = True
            threading.Thread(target=self._start_bg_listen, daemon=True).start()
            return True

    def _start_bg_listen(self):
        if self.status_callback:
            self.status_callback("red", "In Ascolto")
            
        try:
            def callback(indata, frames, time_info, status):
                if not self.is_listening:
                    raise sd.CallbackStop()
                    
                volume = np.sqrt(np.mean(indata**2))
                if self.volume_callback:
                    self.volume_callback(float(volume))
                    
                # Soglia fissa sicura a 0.012 (ignora fruscii ma prende la voce)
                THRESHOLD = 0.012
                
                if volume > THRESHOLD:
                    if self.state == "IDLE":
                        self.state = "SPEAKING"
                        self.audio_data = []
                        self.speech_chunks = 0
                        self.silence_chunks = 0
                        
                    self.audio_data.append(indata.copy())
                    self.speech_chunks += 1
                    self.silence_chunks = 0
                        
                else:
                    if self.state == "SPEAKING":
                        # Coda di silenzio per legare meglio le parole e i respiri
                        self.audio_data.append(indata.copy())
                        self.silence_chunks += 1
                        
                        # 15 blocchi di silenzio continuato = 1.5 secondi esatti di pausa
                        if self.silence_chunks > 15:
                            self.state = "IDLE"
                            audio_copy = self.audio_data.copy()
                            threading.Thread(target=self._process_api, args=(audio_copy,), daemon=True).start()
                            self.audio_data = []
                            self.speech_chunks = 0
                            self.silence_chunks = 0
                            
                # SALVAVITA ASSOLUTO: Se il canale rimane aperto per 10 secondi consecutivi
                # (100 blocchi totali), taglia forzatamente l'audio e invialo subito all'AI!
                if self.state == "SPEAKING" and len(self.audio_data) > 100:
                    self.state = "IDLE"
                    audio_copy = self.audio_data.copy()
                    threading.Thread(target=self._process_api, args=(audio_copy,), daemon=True).start()
                    self.audio_data = []
                    self.speech_chunks = 0
                    self.silence_chunks = 0

            # Frequenza fissa a blocchi da 100 millisecondi per non pesare sulla CPU
            block_100ms = int(SAMPLE_RATE * 0.1)
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, blocksize=block_100ms, callback=callback):
                while self.is_listening:
                    time.sleep(0.1)
                    
        except Exception as e:
            print("Errore mic stream:", e)
            self.is_listening = False
            if self.status_callback:
                self.status_callback("green", "Errore Mic")

    def _process_api(self, frames_list):
        if not client:
            if self.status_callback:
                self.status_callback("yellow", "API Key Assente")
            time.sleep(2)
            if self.is_listening and self.status_callback:
                self.status_callback("red", "In Ascolto")
            return
            
        if self.status_callback:
            self.status_callback("blue", "Trascrizione...")
            
        try:
            audio_np = np.concatenate(frames_list, axis=0)
            
            # Amplifichiamo il volume digitalmente x3 per far sentire "chiara" la voce all'AI
            audio_np = audio_np * 3.0
            
            # Crea il WAV temporaneo (usando clip per evitare distorsioni e scoppi)
            audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
            
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
                
            audio_bytes = wav_io.getvalue()
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            
            if self.translate_to_english:
                prompt_text = "Ascolta l'audio in qualsiasi lingua sia e traduci tutto in lingua INGLESE in maniera ultra-rapida, fluida e naturale. Devi restituire ESCLUSIVAMENTE il testo finale in inglese, non usare nessuna formattazione markdown."
            else:
                prompt_text = "Trascrivi esattamente l'audio. Restituisci ESCLUSIVAMENTE il testo trascritto, non usare formattazione markdown."

            # Ritorniamo a gemini-2.5-flash perché la versione Lite ha limite 0 sul tuo account
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt_text, audio_part]
            )
            
            testo_finale = response.text.replace('```', '').replace('*', '').strip()
            
            if testo_finale:
                if self.clipboard_callback:
                    self.clipboard_callback(testo_finale + " ")
                
                try:
                    time.sleep(0.05)
                    self.keyboard.type(testo_finale + " ")
                except Exception as k_err:
                    print("Errore tastiera:", k_err)
                
        except Exception as e:
            err_msg = str(e)
            print("Errore API/Rete:", err_msg)
            if self.status_callback:
                if "429" in err_msg:
                    self.status_callback("yellow", "Attendi (Limite 429)")
                else:
                    self.status_callback("yellow", f"Err: {err_msg[:24]}")
            time.sleep(3)
            
        if self.is_listening and self.status_callback:
            self.status_callback("red", "In Ascolto")
