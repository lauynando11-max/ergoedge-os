from google import genai

API_KEY = "AIzaSyBkZ47zhVjrYrDdmZBxFs3GGdAY6ZY198o"
client = genai.Client(api_key=API_KEY)

# Usar el modelo gemini-2.5-flash (disponible)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Decime 'Hola, Gemini funciona correctamente' en español",
)

print(response.text)