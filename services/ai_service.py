import os
import openai
import anthropic
from google import genai

def ask_ai(prompt, context, provider="Google (Gemini)", api_key=None, model_id="gemini-2.0-flash-exp"):
    """
    Queries the selected AI Provider for financial advice.
    """
    full_prompt = f"Context: {context}\n\nUser Question: {prompt}\n\nPlease provide a concise, financial-expert response.\nIMPORTANT: If the user asks for calculating metrics, LOOK at the 'Full_Data_CSV' key in the Context before saying you don't have data."
    
    try:
        # --- Google Gemini ---
        if provider == "Google (Gemini)":
            key_to_use = api_key if api_key else os.environ.get("GOOGLE_API_KEY")
            if not key_to_use: return "⚠️ Missing Google API Key."
            
            client = genai.Client(api_key=key_to_use)
            response = client.models.generate_content(model=model_id, contents=full_prompt)
            return response.text

        # --- OpenAI ---
        elif provider == "OpenAI":
            key_to_use = api_key if api_key else os.environ.get("OPENAI_API_KEY")
            if not key_to_use: return "⚠️ Missing OpenAI API Key."

            client = openai.OpenAI(api_key=key_to_use)
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are an expert CFO consultant."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.choices[0].message.content

        # --- Anthropic ---
        elif provider == "Anthropic":
            key_to_use = api_key if api_key else os.environ.get("ANTHROPIC_API_KEY")
            if not key_to_use: return "⚠️ Missing Anthropic API Key."
            
            client = anthropic.Anthropic(api_key=key_to_use)
            response = client.messages.create(
                model=model_id,
                max_tokens=1024,
                system="You are an expert CFO consultant.",
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.content[0].text

        else:
            return "⚠️ Unknown Provider selected."

    except Exception as e:
        return f"⚠️ Error querying {provider}: {str(e)}"
