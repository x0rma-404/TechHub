import os
import json
import ollama

def get_ai_config():
    """Load AI configuration from ai_config/config"""
    # Use absolute path relative to this file's directory to ensure it's found
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(base_dir, 'ai_config', 'config')
    
    default_config = {
        "model": "llama3.2:3b",
        "system_prompt": "You are Dastan, a helpful coding assistant.",
        "temperature": 0.7,
        "stream": False
    }
    
    if not os.path.exists(config_file):
        print(f"⚠️ Config File Not Found at: {config_file}")
        return default_config
        
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Config Load Error: {e}")
        return default_config

def get_ai_response(user_message, system_prompt_override=None):
    """Generate AI response using ollama library and dynamic config"""
    config = get_ai_config()
    
    system_prompt = system_prompt_override if system_prompt_override else config.get('system_prompt')
    
    try:
        response = ollama.chat(
            model=config.get('model', 'llama3.2:3b'),
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            options={
                'temperature': config.get('temperature', 0.7)
            }
        )
        return response['message']['content']
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None
