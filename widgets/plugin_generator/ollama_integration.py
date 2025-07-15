import shutil
import subprocess

def is_ollama_installed():
    return shutil.which("ollama") is not None

def run_ollama_prompt(model: str, prompt: str, stream=False) -> str:
    if not is_ollama_installed():
        raise RuntimeError("❌ Ollama is niet geïnstalleerd. Bezoek https://ollama.com om het te installeren.")

    try:
        print(f"🧠 Vraag aan '{model}': {prompt[:80]}...")
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise RuntimeError("⚠️ Ollama fout: " + result.stderr.decode())

        output = result.stdout.decode()
        if "```python" in output:
            return output.split("```python")[1].split("```")[0].strip()
        elif "```" in output:
            return output.split("```")[1].strip()
        return output.strip()
    except Exception as e:
        raise RuntimeError("⚠️ Kan prompt niet uitvoeren: " + str(e))
