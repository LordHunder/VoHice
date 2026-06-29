# Glaido Clone - Native AI Overlay

Questo è un overlay desktop **sempre in primo piano** (always-on-top) che funziona su Windows o macOS. 
L'applicazione ti permette di dettare frasi e parole in italiano e, tramite le intelligenze artificiali di Google Gemini Pro (1.5 Pro per audio), incollare automaticamente il testo nel campo attivo all'istante (come una casella di testo nel browser, un documento Word o una chat di discord). Include anche la funzionalità opzionale di traduzione fluida e naturale nativa in lingua inglese.

## Prerequisiti

1. Python 3.9 o superiore.
2. Portaudio (di solito è richiesto per abilitare `sounddevice`). Su Windows in genere viene pre-pacchettizzato.

## Installazione

1. Crea o accedi a un ambiente virtuale (consigliato per isolare le librerie).
   ```bash
   python -m venv venv
   # Su Windows (Command Prompt o PowerShell):
   venv\Scripts\activate
   ```
2. Installa le dipendenze fornite nel file `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura l'API Key di Gemini:
   Apri il file `config.py` e sostituisci `"INSERISCI_QUI_LA_TUA_CHIAVE_API"` con una tua API Key. Puoi generarne una accedendo a [Google AI Studio](https://aistudio.google.com/).
   *Alternativa: Esporta la variabile d'ambiente `GEMINI_API_KEY` dal tuo terminale.*

## Come si Usa l'App

1. Avvia l'applicazione digitando nel terminale:
   ```bash
   python overlay.py
   ```
2. Un piccolo widget scuro apparirà in alto a destra. Questo widget rimarrà sempre in cima, indipendentemente dalla finestra in cui stai lavorando. Clicca sulla finestra e trascinalo come meglio preferisci.
3. Posizionati nel campo di testo del programma in cui vuoi scrivere e accertati che il cursore stia lampeggiando lì.
4. **Per trascrivere in italiano**: Controlla che il traduttore sia su "Traduzione: OFF".
5. **Per tradurre in inglese livello madrelingua**: Fai clic sul pulsante della traduzione in modo che dica "Traduzione: ON".
6. Clicca su **⏺ REC**, parla al tuo microfono, e poi clicca **⏹ STOP**.
7. Attendi qualche istante, il led diventerà blu confermando l'attività dell'intelligenza artificiale e subito dopo la tastiera magicamente digiterà il testo senza traduzioni letterali rigide!
