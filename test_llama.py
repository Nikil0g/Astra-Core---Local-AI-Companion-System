from llama_cpp import Llama

# Путь к твоей модели (уточни, если файл лежит в другом месте)
model_path = "C:/AstraAI/models/saiga_llama3_8b.Q8_0.gguf"

print("Пытаюсь загрузить модель...")
try:
    llm = Llama(model_path=model_path, n_gpu_layers=99, verbose=True)
    print("Модель загружена успешно!")
except Exception as e:
    print(f"Ошибка загрузки: {e}")