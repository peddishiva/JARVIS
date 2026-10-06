import pyttsx3
import speech_recognition as sr
import eel
import time

def speak(text):
    text = str(text)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    eel.DisplayMessage(text)
    engine.say(text)
    eel.receiverText(text)
    engine.runAndWait()
    
    
def takecommand():

    r = sr.Recognizer()
 
    with sr.Microphone() as source:
        print('listening...')
        eel.DisplayMessage('listening...')
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        
        audio = r.listen(source, 10, 6)

    try:
        print('Recognizing...')
        eel.DisplayMessage('Recognizing...')
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        time.sleep(3)
        
        
    except Exception as e:
        return ""

    return query.lower()

@eel.expose
def allCommands(message=1):
    
    if message == 1:
        query = takecommand()
        print(query)
        eel.senderText(query)
    else:
         query = message
         eel.senderText(query)
    
    try:
        normalized_query = query.lower().strip() if isinstance(query, str) else str(query).lower().strip()
        
        if "open" in normalized_query:
            from engine.features import openCommand
            openCommand(normalized_query)
        elif "on youtube" in normalized_query:
            from engine.features import PlayYoutube
            PlayYoutube(query)
        elif "send a message" in normalized_query or "phone call" in normalized_query or "video call" in normalized_query:
            from engine.features import findContact, whatsApp
            message = ""
            contact_no, name = findContact(normalized_query)
            if(contact_no != 0):

                if "send a message" in normalized_query:
                    message = 'message'
                    speak("what message to send")
                    query = takecommand()
                    
                elif "phone call" in normalized_query:
                    message = 'call'
                else:
                    message = 'video call'
                    
                whatsApp(contact_no, query, message, name)

        else:
            from engine.features import chatBot
            chatBot(query)
    except:
        print("error")
        
    eel.ShowHood()