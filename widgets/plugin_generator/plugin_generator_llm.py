from .ollama_integration import is_ollama_installed, run_ollama_prompt
from .plugin_template_fallback import generate_fallback_main_py

def run_model_prompt(prompt: str, classname: str, model: str, log_func) -> str:
    try:
        if is_ollama_installed():
            log_func(f"🧠 Prompt naar model '{model}'...")
            code = run_ollama_prompt(model, f"Schrijf een PyQt6 QWidget class genaamd '{classname}' die dit doet: {prompt}")
            log_func("✅ Code gegenereerd via Ollama")
        else:
            log_func("⚠️ Ollama niet beschikbaar — fallback gebruikt")
            code = generate_fallback_main_py(classname, prompt)
        return code
    except Exception as e:
        log_func(f"❌ AI-fout: {e}")
        raise
