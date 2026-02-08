import os
import json
import ollama

def get_ai_config():
    """Load AI configuration from ai_config/config and ai_config/prompt.txt"""
    # Use absolute path relative to this file's directory to ensure it's found
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(base_dir, 'ai_config', 'config')
    prompt_file = os.path.join(base_dir, 'ai_config', 'prompt.txt')
    
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
            config = json.load(f)
        
        # Load system prompt from separate file if specified
        if 'prompt_file' in config:
            prompt_path = os.path.join(base_dir, 'ai_config', config['prompt_file'])
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as pf:
                    config['system_prompt'] = pf.read().strip()
            else:
                print(f"⚠️ Prompt File Not Found at: {prompt_path}")
                config['system_prompt'] = default_config['system_prompt']
        
        return config
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
